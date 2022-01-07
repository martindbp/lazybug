import pickle
import logging
import random
from math import floor

import cv2
import torch
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from torch import optim
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, random_split
import torchmetrics
from tqdm import tqdm
from merkl import task

import vocab


class OCRDataset(Dataset):
    def __init__(self, out_width, images_dir, masks_dir, text_positions, vocab):
        self.out_width = out_width
        self.images_dir = images_dir
        self.masks_dir = masks_dir
        self.text_positions = text_positions
        self.vocab = vocab
        logging.info(f'Creating dataset with {len(images_dir.files)} examples')

    def __len__(self):
        return len(self.images_dir.files)

    @classmethod
    def preprocess_img(self, img):
        # Change HWC to CHW
        img = img.astype(float) / 255
        return img.transpose((2, 0, 1))

    @classmethod
    def preprocess_mask(self, mask):
        # Change HWC to CHW
        mask = mask / 255
        mask = np.expand_dims(mask, axis=2)
        return mask.transpose((2, 0, 1))

    def __getitem__(self, i):
        img_file, mask_file = self.images_dir.files[i], self.masks_dir.files[i]

        img_orig = cv2.imread(img_file, cv2.IMREAD_UNCHANGED)
        mask_orig = cv2.imread(mask_file, cv2.IMREAD_GRAYSCALE)
        # Change HWC to CHW
        img = self.preprocess_img(img_orig)
        mask = self.preprocess_mask(mask_orig)

        positions = self.text_positions[i]

        # Width after 4 max-pools, then a size-5 convolution with no padding -> minus 2 or each side = 4
        embedding_width = self.out_width // (2*2*2*2) - 4
        embedding = np.zeros((len(self.vocab), embedding_width), dtype=float)
        # Mask is the xs we want to use to calculate the loss with, and ignore the rest
        embedding_mask = np.zeros((len(self.vocab), embedding_width), dtype=bool)

        def _embedded_pos(pos):
            embedded_pos = pos / (2*2*2*2) - 2  # 4x max pooling minus conv shinking one side
            # Since we're chopping off 2 at the end, we can end up outside the embedding
            embedded_pos = min(embedded_pos, embedding_width-1)
            embedded_pos = floor(embedded_pos)
            return embedded_pos

        for char, start_x, end_x in positions:
            encoded = self.vocab.encode_char_components(char)
            pos_x_in_image = (start_x + end_x) / 2
            pos_x_in_embedding = _embedded_pos(pos_x_in_image)
            #print(pos_x_in_image / self.out_width, pos_x_in_embedding / embedding_width)
            #print(f'char at {pos_x_in_image}, {pos_x_in_embedding}')
            embedding[:, pos_x_in_embedding] = encoded
            embedding_mask[:, pos_x_in_embedding] = True

        for (_, _, start_x), (_, end_x, _) in zip(positions[:-1], positions[1:]):
            pos_x_in_image = (start_x + end_x) / 2
            #print(f'empty at {pos_x_in_image}, {_embedded_pos(pos_x_in_image)}')
            embedding_mask[:, _embedded_pos(pos_x_in_image)] = True

        CHAR_WIDTH = 60

        for x in range(positions[0][1], 0, -CHAR_WIDTH):
            pos_x_in_embedding = _embedded_pos(x)
            #print(f'empty at {x}, {pos_x_in_embedding}')
            embedding_mask[:, pos_x_in_embedding] = True

        for x in range(positions[-1][2], self.out_width, CHAR_WIDTH):
            pos_x_in_embedding = _embedded_pos(x)
            #print(f'empty at {x}, {pos_x_in_embedding}')
            embedding_mask[:, pos_x_in_embedding] = True

        #cv2.imshow("img", img_orig)
        #cv2.waitKey()
        #breakpoint()

        return {
            'image': torch.from_numpy(img).type(torch.FloatTensor),
            'mask': torch.from_numpy(mask).type(torch.FloatTensor),
            'embedding': torch.from_numpy(embedding).type(torch.LongTensor),
            'embedding_mask': torch.from_numpy(embedding_mask).type(torch.BoolTensor),
        }


class DoubleConv(nn.Module):
    """(convolution => [BN] => ReLU) * 2"""

    def __init__(self, in_channels, out_channels, mid_channels=None):
        super().__init__()
        if not mid_channels:
            mid_channels = out_channels
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)


class Down(nn.Module):
    """Downscaling with maxpool then double conv"""

    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels)
        )

    def forward(self, x):
        return self.maxpool_conv(x)


class TransposeLinear(nn.Module):
    def __init__(self, in_channels, out_channels, swap_dim1, swap_dim2):
        super().__init__()
        self.swap_dim1 = swap_dim1
        self.swap_dim2 = swap_dim2
        self.linear = nn.Linear(in_channels, out_channels)

    def forward(self, x):
        transposed = torch.transpose(x, self.swap_dim1, self.swap_dim2)
        x = self.linear(transposed)
        return torch.transpose(x, self.swap_dim1, self.swap_dim2)  # transpose back


class FinalDown(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, padding=0),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            TransposeLinear(out_channels, out_channels, 1, 3),
        )

    def forward(self, x):
        return self.conv(x)


class OCREmbedding(nn.Module):
    def __init__(self, n_channels, vocab_size):
        super().__init__()
        self.inc = DoubleConv(n_channels, 64)  # height=80
        self.down1 = Down(64, 128)  # height=40
        self.down2 = Down(128, 256)  # height=20
        self.down3 = Down(256, 512)  # height=10
        self.down4 = Down(512, 1024)  # height=5
        self.down5 = FinalDown(1024, vocab_size, kernel_size=5)  # height=1
        #self.up1 = FinalUp(1024, 512, kernel_size=5)
        #self.up2 = Up(512, 256)
        #self.up3 = Up(256, 128)
        #self.up4 = Up(128, 64)
        #self.outc = OutConv(64, n_classes)

    def forward(self, x):
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        x6 = self.down5(x5)
        return x6
        #x = self.up1(x5, x4)
        #x = self.up2(x, x3)
        #x = self.up3(x, x2)
        #x = self.up4(x, x1)
        #logits = self.outc(x)
        #return logits


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def _get_unet(vocab_size):
    net = OCREmbedding(n_channels=3, vocab_size=vocab_size)
    net.to(device=device)
    return net


class TrainingStateSerializer:
    @classmethod
    def dumps(cls, training_state):
        out = dict(training_state)
        for key in ['net', 'optimizer', 'scheduler']:
            out[key] = out[key].state_dict()
        return pickle.dumps(out)

    @classmethod
    def loads(cls, data):
        training_state = pickle.loads(data)
        vocab_size = training_state['vocab_size']
        net = _get_unet(vocab_size)
        net.load_state_dict(training_state['net'])
        optimizer = optim.Adam(net.parameters())
        optimizer.load_state_dict(training_state['optimizer'])
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer)
        scheduler.load_state_dict(training_state['scheduler'])
        return {
            'net': net,
            'optimizer': optimizer,
            'scheduler': scheduler,
            'vocab_size': vocab_size,
        }


def seed_worker(worker_id):
    worker_seed = torch.initial_seed() % 2**32
    np.random.seed(worker_seed)
    random.seed(worker_seed)


def cross_entroy_multi_class_loss(pred, labels):
    return (
        -labels * torch.log(pred)
        -(1-labels) * torch.log(1-pred) 
    )


def forward(net, batch, vocab, no_grad=False, return_probs_labels=False):
    imgs = batch['image']
    true_masks = batch['mask']
    embeddings = batch['embedding']
    embedding_masks = batch['embedding_mask']
    embedding_masks = embedding_masks.to(device=device, dtype=torch.bool)
    imgs = imgs.to(device=device, dtype=torch.float32)

    if no_grad:
        with torch.no_grad():
            embeddings_pred = net(imgs)
    else:
        embeddings_pred = net(imgs)
    embeddings_pred = embeddings_pred.squeeze()

    embeddings_selected = torch.masked_select(embeddings, embedding_masks)
    embeddings_selected = embeddings_selected.to(device=device, dtype=torch.float32)
    pred_embeddings_selected = torch.masked_select(embeddings_pred, embedding_masks)
    #pos_weight = 5 * torch.ones([pred_embeddings_selected.shape[0]]).to(device)
    #criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    tiled_weights = vocab.weights.tile(embedding_masks[:, 0, :].sum())
    criterion = nn.BCEWithLogitsLoss(pos_weight=tiled_weights)
    #criterion = nn.BCEWithLogitsLoss()
    loss = criterion(pred_embeddings_selected, embeddings_selected)
    if return_probs_labels:
        return loss, torch.sigmoid(pred_embeddings_selected), embeddings_selected

    return loss


@task(serializer=TrainingStateSerializer, deps=[vocab])
def new_train_epoch(
    images_dir,
    masks_dir,
    text_positions,
    out_width,
    vocab,
    epoch,
    batch_size=1,
    initial_lr=0.0001,
    val_percent=0.1,
    training_state={},
):
    vocab.set_device(device)
    torch.manual_seed(42)
    random.seed(42)
    np.random.seed(42)
    torch.use_deterministic_algorithms(True)

    if 'net' not in training_state:
        net = _get_unet(len(vocab))
    else:
        net = training_state['net']

    dataset = OCRDataset(
        out_width,
        images_dir,
        masks_dir,
        text_positions,
        vocab,
    )
    n_val = int(len(dataset) * val_percent)
    n_train = len(dataset) - n_val
    train, val = random_split(dataset, [n_train, n_val])
    num_workers = 0
    train_loader = DataLoader(
        train,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True,
        worker_init_fn=seed_worker,
    )
    val_loader = DataLoader(
        val,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
        drop_last=True,
        worker_init_fn=seed_worker,
    )

    global_step = 0

    logging.info(f'''Starting training:
        Batch size:      {batch_size}
        Learning rate:   {initial_lr}
        Training size:   {n_train}
        Validation size: {n_val}
        Device:          {device.type}
    ''')

    optimizer = training_state.get('optimizer', optim.Adam(net.parameters(), lr=initial_lr))
    scheduler = training_state.get('scheduler', optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'max', patience=2))

    net.train()

    epoch_loss = 0
    print(f'Starting epoch {epoch+1}')
    with tqdm(total=n_train, desc=f'Epoch {epoch + 1}', unit='img') as pbar:
        for batch in train_loader:
            loss = forward(net, batch, vocab)
            epoch_loss += loss.item()

            pbar.set_postfix(**{'loss (batch)': loss.item()})

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_value_(net.parameters(), 0.1)
            optimizer.step()

            pbar.update(batch['image'].shape[0])
            global_step += 1
            if global_step % (n_train // (10 * batch_size)) == 0:
                for tag, value in net.named_parameters():
                    tag = tag.replace('.', '/')
                val_score = eval_net(net, val_loader, device, vocab)
                scheduler.step(val_score)
                print(' Validation cross entropy: {}'.format(val_score))

    print(f'Epoch loss: {epoch_loss}')
    training_state = {
        'net': net,
        'optimizer': optimizer,
        'scheduler': scheduler,
        'vocab_size': len(vocab),
    }
    return training_state


def eval_net(net, loader, device, vocab):
    """Evaluation without the densecrf with the dice coefficient"""
    net.eval()
    #mask_type = torch.float32
    n_val = len(loader)  # the number of batch
    tot = 0

    all_probs, all_labels = None, None
    with tqdm(total=n_val, desc='Validation round', unit='batch', leave=False) as pbar:
        for batch in loader:
            loss, probs, labels = forward(net, batch, vocab, no_grad=True, return_probs_labels=True)
            if all_probs is None:
                all_probs = probs
                all_labels = labels
            else:
                all_probs = torch.cat((all_probs, probs))
                all_labels = torch.cat((all_labels, labels))

            tot += loss.item()
            pbar.update()

    all_pred = (all_probs > 0.5).float().to('cpu')
    all_labels = all_labels.type(torch.LongTensor).to('cpu')
    print(f'F1: {torchmetrics.F1()(all_pred, all_labels).item()}')
    #print(f'AUC: {torchmetrics.AUC(reorder=True)(all_probs.to("cpu"), all_labels).item()}')
    print(f'Precision: {torchmetrics.Precision()(all_pred, all_labels)}')
    print(f'Recall: {torchmetrics.Recall()(all_pred, all_labels)}')
    #print(all_pred[:600])
    #print(all_labels[:600])

    net.train()
    return tot / n_val


@task
def predict_img(net, img):
    net.eval()
    img = OCRDataset.preprocess_img(img)
    img = torch.from_numpy(img)
    img = img.unsqueeze(0)
    img = img.to(device=device, dtype=torch.float32)

    with torch.no_grad():
        breakpoint()
        embedding = net(img)

        probs = torch.sigmoid(embedding)
        probs = probs.squeeze(0)
        breakpoint()
        print(probs)
        return probs
