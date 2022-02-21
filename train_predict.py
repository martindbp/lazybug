import io
import random
import cv2
from merkl import task, FileRef, pipeline, Future
import generate_dataset
#from unet.train import train_epoch
#from unet.predict import predict_img
import torch
import vocab
from vocab import Vocab
import new_model
from corpus import get_corpus

from unet.train import train_net
from unet.predict import predict_img as predict_img_unet
from unet.unet import UNet

from PIL import Image

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

@task
def get_net(training_state):
    return training_state['net']


@task(outs=2)
def predict_img(net, img, threshold):
    pil_img = Image.fromarray(img)
    return predict_img_unet(net, pil_img, device, out_threshold=threshold)


class NetSerializer:
    @classmethod
    def dumps(cls, net_path):
        with open(net_path, 'rb') as f:
            return f.read()

    @classmethod
    def loads(cls, data):
        net = UNet(n_channels=3, n_classes=1, bilinear=True)
        net.load_state_dict(torch.load(io.BytesIO(data)))
        net.to(device=device)
        net.eval()
        return net


@task(serializer=NetSerializer)
def train_unet(images_dir, masks_dir, epochs=8, lr=0.001, batch_size=4, net=None):
    if net is None:
        net = UNet(n_channels=3, n_classes=1, bilinear=True)
        net.to(device=device)

    return train_net(
        net=net,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        device=device,
        img_scale=1,
        val_percent=0.1,
        dir_img=images_dir,
        dir_mask=masks_dir,
    )


@pipeline(cache_in_memory=True)
def train_pipeline():
    seed = 42
    corpus = get_corpus(seed=seed)
    images_dir, masks_dir, characters = generate_dataset.pipeline(corpus, 30000, 1024, 80, seed=seed)

    net = train_unet(images_dir, masks_dir)
    net >> f'data/remote/private/text_segmentation_model-{net.hash}.pth'
    with open('data/remote/private/text_segmentation_model.pth.hash', 'w') as f:
        f.write(net.hash)

    return net


def finetune_pipeline():
    seed = 42
    corpus = get_corpus(seed=seed)
    images_dir, masks_dir, characters = generate_dataset.pipeline(corpus, 30000, 1024, 80, seed=seed, fill_with_synthetic=False)

    net = _get_latest_net()
    net = train_unet(images_dir, masks_dir, epochs=4, lr=0.0005, net=net)
    net >> f'data/remote/private/text_segmentation_model-{net.hash}.pth'
    with open('data/remote/private/text_segmentation_model.pth.hash', 'w') as f:
        f.write(net.hash)

    return net

imread = task(outs=1)(cv2.imread)

def _get_latest_net():
    with open('data/remote/private/text_segmentation_model.pth.hash', 'r') as f:
        net_hash = f.read().strip()

    net = Future.from_file(f'data/remote/private/text_segmentation_model-{net_hash}.pth')
    return net

def predict_pipeline_path(img_path, net=None):
    if net is None:
        net = _get_latest_net()

    img = imread(FileRef(img_path))
    mask, probs = predict_img(net, img, 0.2)
    cv2.imshow("mask", mask.eval())
    probs = probs.eval()
    probs = (255*probs).astype('uint8')
    cv2.imshow("probs", probs)
    cv2.imshow("img", img.eval())
    cv2.waitKey()
    return mask, probs


def predict_img_pipeline(img, net=None):
    if net is None:
        net = _get_latest_net()

    mask, probs = predict_img(net, img, 0.2)
    return mask, probs


def new_predict_pipeline_path(img_path):
    net = new_train_pipeline()

    img = imread(FileRef(img_path), cv2.IMREAD_UNCHANGED)
    embedding = new_model.predict_img(net, img)
    print(embedding)
    #cv2.imshow("mask", mask.eval())
    #probs = probs.eval()
    #probs = (255*probs).astype('uint8')
    #cv2.imshow("probs", probs)
    #cv2.imshow("img", img.eval())
    #cv2.waitKey()
    return embedding


@task(deps=[vocab])
def get_vocab():
    vocab = Vocab()
    vocab.load()
    return vocab


@pipeline(cache_in_memory=True)
def new_train_pipeline():
    out_width = 1024
    images_dir, masks_dir, text_positions = generate_dataset.pipeline(10000, out_width, 80, seed=42)

    vocab = get_vocab()

    training_state = {}
    for epoch in range(6):
        training_state = new_model.new_train_epoch(
            images_dir,
            masks_dir,
            text_positions,
            out_width,
            vocab,
            epoch,
            training_state=training_state,
            batch_size=5,
        )
        training_state.cache_temporarily = True

    # Store the last iteration permanently
    training_state.cache_temporarily = False

    return get_net(training_state)
