import os
import argparse
import librosa
import numpy as np
import soundfile as sf
import torch
from tqdm import tqdm

from vocal_remover.lib import dataset
from vocal_remover.lib import nets
from vocal_remover.lib import spec_utils
from vocal_remover.lib import utils


class Separator(object):

    def __init__(self, model, device=None, batchsize=1, cropsize=256, postprocess=False):
        self.model = model
        self.offset = model.offset
        self.device = device
        self.batchsize = batchsize
        self.cropsize = cropsize
        self.postprocess = postprocess

    def _postprocess(self, X_spec, mask):
        if self.postprocess:
            mask_mag = np.abs(mask)
            mask_mag = spec_utils.merge_artifacts(mask_mag)
            mask = mask_mag * np.exp(1.j * np.angle(mask))

        y_spec = X_spec * mask
        v_spec = X_spec - y_spec

        return y_spec, v_spec

    def _separate(self, X_spec_pad, roi_size):
        X_dataset = []
        patches = (X_spec_pad.shape[2] - 2 * self.offset) // roi_size
        for i in range(patches):
            start = i * roi_size
            X_spec_crop = X_spec_pad[:, :, start:start + self.cropsize]
            X_dataset.append(X_spec_crop)

        X_dataset = np.asarray(X_dataset)

        self.model.eval()
        with torch.no_grad():
            mask_list = []
            # To reduce the overhead, dataloader is not used.
            for i in tqdm(range(0, patches, self.batchsize)):
                X_batch = X_dataset[i: i + self.batchsize]
                X_batch = torch.from_numpy(X_batch).to(self.device)

                mask = self.model.predict_mask(X_batch)

                mask = mask.detach().cpu().numpy()
                mask = np.concatenate(mask, axis=2)
                mask_list.append(mask)

            mask = np.concatenate(mask_list, axis=2)

        return mask

    def separate(self, X_spec):
        n_frame = X_spec.shape[2]
        pad_l, pad_r, roi_size = dataset.make_padding(n_frame, self.cropsize, self.offset)
        X_spec_pad = np.pad(X_spec, ((0, 0), (0, 0), (pad_l, pad_r)), mode='constant')
        X_spec_pad /= np.abs(X_spec).max()

        mask = self._separate(X_spec_pad, roi_size)
        mask = mask[:, :, :n_frame]

        y_spec, v_spec = self._postprocess(X_spec, mask)

        return y_spec, v_spec

    def separate_tta(self, X_spec):
        n_frame = X_spec.shape[2]
        pad_l, pad_r, roi_size = dataset.make_padding(n_frame, self.cropsize, self.offset)
        X_spec_pad = np.pad(X_spec, ((0, 0), (0, 0), (pad_l, pad_r)), mode='constant')
        X_spec_pad /= X_spec_pad.max()

        mask = self._separate(X_spec_pad, roi_size)

        pad_l += roi_size // 2
        pad_r += roi_size // 2
        X_spec_pad = np.pad(X_spec, ((0, 0), (0, 0), (pad_l, pad_r)), mode='constant')
        X_spec_pad /= X_spec_pad.max()

        mask_tta = self._separate(X_spec_pad, roi_size)
        mask_tta = mask_tta[:, :, roi_size // 2:]
        mask = (mask[:, :, :n_frame] + mask_tta[:, :, :n_frame]) * 0.5

        y_spec, v_spec = self._postprocess(X_spec, mask)

        return y_spec, v_spec


class MainProcessor:
    @staticmethod
    def mainu(audio_file_path, model_path='vocal_remover/models/baseline.pth', args=None):
        if args is None:
            args = argparse.Namespace()
            args.gpu = -1
            args.sr = 44100
            args.n_fft = 2048
            args.hop_length = 1024
            args.batchsize = 4
            args.cropsize = 256
            args.output_image = False
            args.tta = False
            args.output_dir = ""

        print('loading model...', end=' ')
        device = torch.device('cpu')
        if args.gpu >= 0:
            if torch.cuda.is_available():
                device = torch.device('cuda:{}'.format(args.gpu))
            elif torch.backends.mps.is_available() and torch.backends.mps.is_built():
                device = torch.device('mps')
        model = nets.CascadedNet(args.n_fft, args.hop_length, 32, 128, True)
        model.load_state_dict(torch.load(model_path, map_location='cpu'))
        model.to(device)
        print('done')

        print('loading wave source...', end=' ')
        X, sr = librosa.load(
            audio_file_path, sr=args.sr, mono=False, dtype=np.float32, res_type='kaiser_fast'
        )
        basename = os.path.splitext(os.path.basename(audio_file_path))[0]
        print('done')

        if X.ndim == 1:
            # mono to stereo
            X = np.asarray([X, X])

        print('stft of wave source...', end=' ')
        X_spec = spec_utils.wave_to_spectrogram(X, args.hop_length, args.n_fft)
        print('done')

        sp = Separator(
            model=model,
            device=device,
            batchsize=args.batchsize,
            cropsize=args.cropsize,
            # postprocess=args.postprocess
        )

        if args.tta:
            y_spec, v_spec = sp.separate_tta(X_spec)
        else:
            y_spec, v_spec = sp.separate(X_spec)

        print('validating output directory...', end=' ')
        output_dir = args.output_dir
        if output_dir != "":  # modifies output_dir if theres an arg specified
            output_dir = output_dir.rstrip('/') + '/'
            os.makedirs(output_dir, exist_ok=True)
        print('done')

        print('inverse stft of instruments...', end=' ')
        wave = spec_utils.spectrogram_to_wave(y_spec, hop_length=args.hop_length)
        print('done')
        sf.write('{}{}_Instruments.wav'.format(output_dir, basename), wave.T, sr)

        print('inverse stft of vocals...', end=' ')
        wave = spec_utils.spectrogram_to_wave(v_spec, hop_length=args.hop_length)
        print('done')
        sf.write('{}{}_Vocals.wav'.format(output_dir, basename), wave.T, sr)

if __name__ == '__main__':
    MainProcessor.mainu('/Users/aidaizhusup/Downloads/n1.mp3')
