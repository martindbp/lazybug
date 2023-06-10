from itertools import groupby

import cv2
import torch
import numpy as np
from hanziconv import HanziConv
from torch.nn import functional as F

from cnocr import CnOcr
from cnocr.utils import pad_img_seq, to_numpy, gen_length_mask
from cnocr.models.ocr_model import OcrModel

def _predict(self, img_list):
    img_lengths = torch.tensor([img.shape[2] for img in img_list])
    imgs = pad_img_seq(img_list)
    if self._model_backend == 'pytorch':
        with torch.no_grad():
            out = self._model(
                imgs, img_lengths, candidates=self._candidates, return_preds=True
            )
    else:  # onnx
        out = _onnx_predict(self, imgs, img_lengths)

    return out

def _onnx_predict(self, imgs, img_lengths):
    ort_session = self._model
    ort_inputs = {
        ort_session.get_inputs()[0].name: to_numpy(imgs),
        ort_session.get_inputs()[1].name: to_numpy(img_lengths),
    }
    ort_outs = ort_session.run(None, ort_inputs)
    out = {
        'logits': torch.from_numpy(ort_outs[0]),
        'output_lengths': torch.from_numpy(ort_outs[1]),
    }
    out['logits'] = OcrModel.mask_by_candidates(
        out['logits'], self._candidates, self._vocab, self._letter2id
    )

    preds, char_probs, prob_distributions = ctc_best_path(self, out['logits'], self._vocab, out['output_lengths'])
    out["preds"] = preds
    out["char_probs"] = char_probs
    out["prob_distributions"] = prob_distributions
    return out


def ctc_best_path(
    self,
    logits,
    vocab,
    input_lengths=None,
):
    blank = len(vocab)
    # compute softmax
    probs = F.softmax(logits.permute(0, 2, 1), dim=1)
    # get char indices along best path
    best_path = torch.argmax(probs, dim=1)  # [N, T]

    if input_lengths is not None:
        length_mask = gen_length_mask(input_lengths, probs.shape).to(
                device=probs.device
                )  # [N, 1, T]
        probs.masked_fill_(length_mask, 1.0)
        best_path.masked_fill_(length_mask.squeeze(1), blank)

    orig_probs = probs
    # define word proba as min proba of sequence
    probs, _ = torch.max(probs, dim=1)  # [N, T]
    probs, _ = torch.min(probs, dim=1)  # [N]

    words = []
    out_prob_distributions = []
    out_char_probs = []
    for sequence in best_path:
        # collapse best path (using itertools.groupby), map to chars, join char list to string
        collapsed = [vocab[k] for k, _ in groupby(sequence) if k != blank]
        curr_idx = 0
        collapsed_char_probs = []
        collapsed_prob_distributions = []
        for char_code, char_codes in groupby(sequence):
            char_codes = list(char_codes)
            if char_code.item() == blank:
                curr_idx += len(char_codes)
                continue

            prob_distribution = orig_probs[0, :, curr_idx].detach().cpu().numpy()
            char_prob = prob_distribution[char_code.item()]
            collapsed_prob_distributions.append(prob_distribution)
            collapsed_char_probs.append(char_prob)
            curr_idx += len(char_codes)

        assert len(collapsed_prob_distributions) == len(collapsed)
        out_prob_distributions.append(collapsed_prob_distributions)
        out_char_probs.append(collapsed_char_probs)
        words.append(collapsed)

    return list(zip(words, probs.tolist())), np.array(out_char_probs), np.array(out_prob_distributions)


class CnOcrShim(CnOcr):
    traditional = False

    def __init__(self, traditional=False, input_font_height=None):
        self.traditional = traditional
        model_name = 'chinese_cht_PP-OCRv3' if traditional else 'densenet_lite_136-fc'
        super().__init__(rec_model_name=model_name)

        if getattr(self.rec_model, '_vocab', None) is None:
            d = self.rec_model.postprocess_op.dict
            
            self.alphabet = [None] * (max(d.values()) + 1)
            for val, idx in d.items():
                self.alphabet[idx] = val
        else:
            self.alphabet = self.rec_model._vocab

        self.input_font_height = input_font_height

    def resize(self, img):
        if self.input_font_height is None:
            return img

        # Some models have an optimal text height at 32 pixels, so resize text to that size
        scale_factor = 32 / self.input_font_height
        resized = cv2.resize(img, (int(img.shape[1] * scale_factor), int(img.shape[0] * scale_factor)), interpolation=cv2.INTER_LANCZOS4)
        cv2.imshow('resized', resized)
        cv2.waitKey()
        return resized

    def ocr_fn(self, img, *args):
        #img = self.resize(img)
        if self.traditional:
            img = 255 - img  # make it black text on white background
            text, char_probs, prob_distribution = self.ocr_for_single_lines_probs_CnOCR_onnx(255 - img, *args)
            text, prob_distribution = self.convert_to_simplified(text, prob_distribution)
            return text, char_probs, prob_distribution
        else:
            return self.ocr_for_single_lines_probs_CnOCR_pytorch(img, *args)

    def convert_to_simplified(self, text, probs):
        # We convert any traditional chars to simplified in text and the probs
        sm_text = HanziConv.toSimplified(text)
        print(text, sm_text)

        # We set prob(simplified(char)) = prob(char) + prob(simplified(char)) for all chars in the alphabet, and set prob(char) to 0
        for i, c in enumerate(text):
            c_simp = HanziConv.toSimplified(c)
            if c_simp != c and c_simp in self.alphabet:
                probs[i][self.alphabet.index(c_simp)] += probs[i][self.alphabet.index(c)]
                probs[i][self.alphabet.index(c)] = 0

        return sm_text, probs

    def ocr_for_single_lines_probs_CnOCR_onnx(self, img, *args):
        model = self.rec_model

        batch_size = 1
        img_list = [img]
        if len(img_list) == 0:
            return []

        img_list = [model._prepare_img(img) for img in img_list]

        img_num = len(img_list)
        # Calculate the aspect ratio of all text bars
        width_list = []
        for img in img_list:
            width_list.append(img.shape[1] / float(img.shape[0]))
        # Sorting can speed up the recognition process
        indices = np.argsort(np.array(width_list))
        rec_res = [['', 0.0]] * img_num
        prob_distributions = []
        for beg_img_no in range(0, img_num, batch_size):
            end_img_no = min(img_num, beg_img_no + batch_size)
            norm_img_batch = []
            max_wh_ratio = 0
            for ino in range(beg_img_no, end_img_no):
                h, w = img_list[indices[ino]].shape[0:2]
                wh_ratio = w * 1.0 / h
                max_wh_ratio = max(max_wh_ratio, wh_ratio)
            for ino in range(beg_img_no, end_img_no):
                if model.rec_algorithm != "SRN" and model.rec_algorithm != "SAR":
                    norm_img = model.resize_norm_img(
                        img_list[indices[ino]], max_wh_ratio
                    )
                    norm_img = norm_img[np.newaxis, :]
                    norm_img_batch.append(norm_img)
            norm_img_batch = np.concatenate(norm_img_batch)
            norm_img_batch = norm_img_batch.copy()

            input_dict = dict()
            input_dict[model.input_tensor.name] = norm_img_batch
            outputs = model.predictor.run(model.output_tensors, input_dict)
            preds = outputs[0]
            prob_distributions.append(preds)

            rec_result = model.postprocess_op(preds)
            for rno in range(len(rec_result)):
                rec_res[indices[beg_img_no + rno]] = rec_result[rno]

        prob_distribution = prob_distributions[0][0]
        prob_distribution = np.sqrt(prob_distribution)
        text = rec_res[0][0]
        #for i in range(len(text)):
            #prob_distribution[i, :] = prob_distribution[i, :] / prob_distribution[i, :].sum()
        char_probs = prob_distribution.max(axis=-1)
        return text, char_probs, prob_distribution


    def ocr_for_single_lines_probs_CnOCR_pytorch(self, img, *args):
        """ This code is pulled from recognizer.py in CnOCR. We modify it to return
        the probability distributions over each characters since the official API doesn't """
        model = self.rec_model

        batch_size = 1
        img_list = [img]

        if len(img_list) == 0:
            return []

        img_list = [model._prepare_img(img) for img in img_list]
        img_list = [model._transform_img(img) for img in img_list]

        should_sort = batch_size > 1 and len(img_list) // batch_size > 1

        if should_sort:
            sorted_idx_list = sorted(
                range(len(img_list)), key=lambda i: img_list[i].shape[2]
            )
            sorted_img_list = [img_list[i] for i in sorted_idx_list]
        else:
            sorted_idx_list = range(len(img_list))
            sorted_img_list = img_list

        idx = 0
        sorted_out = []
        while idx * batch_size < len(sorted_img_list):
            imgs = sorted_img_list[idx * batch_size : (idx + 1) * batch_size]
            try:
                batch_out = _predict(model, imgs)
            except Exception as e:
                batch_out = {'preds': [([''], 0.0)] * len(imgs)}
            sorted_out.append(batch_out)
            idx += 1

        out = [None] * len(sorted_out)
        for idx, pred in zip(sorted_idx_list, sorted_out):
            out[idx] = pred

        res = []
        probs = []
        prob_distributions = []
        char_probs = []
        for line in out:
            prob_distribution = line['prob_distributions'].squeeze(0)
            prob_distribution = prob_distribution[..., :-1]
            prob_distributions.append(prob_distribution)
            char_probs.append(prob_distribution.max(axis=-1) if len(prob_distribution) > 0 else [])
            chars, prob = line['preds'][0]
            chars = [c if c != '<space>' else ' ' for c in chars]
            probs.append(prob)
            res.append(''.join(chars))

        text = ''.join(res[0])
        prob_distribution = prob_distributions[0]
        char_probs = char_probs[0]
        return text, char_probs, prob_distribution
