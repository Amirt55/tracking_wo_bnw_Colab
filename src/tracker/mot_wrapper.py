from torch.utils.data import Dataset
import torch

from .mot_tracks import MOT_Tracks
from .mot_sequence import MOT_Sequence


class MOT_Wrapper(Dataset):
	"""Multiple Object Tracking Dataset.

	Wrapper class for combining (MOT_Sequence) or MOT_Tracks into one dataset
	"""

	def __init__(self, image_set, dataloader):
		self.prec_conv = False
		self.image_set = image_set

		self._train_folders = ['MOT17-02', 'MOT17-04', 'MOT17-05', 'MOT17-09', 'MOT17-10',
			'MOT17-11', 'MOT17-13']
		#self._train_folders = ['MOT17-02']
		self._test_folders = ['MOT17-01', 'MOT17-03', 'MOT17-06', 'MOT17-07',
			'MOT17-08', 'MOT17-12', 'MOT17-14']

		assert image_set in ["train", "test"], "[!] Invalid image set: {}".format(image_set)

		self._dataloader = dataloader()

		if image_set == "train":
			for seq in self._train_folders:
				d = dataloader(seq)
				for sample in d.data:
					self._dataloader.data.append(sample)
		if image_set == "test":
			for seq in self._test_folders:
				d = dataloader(seq)
				for sample in d.data:
					self._dataloader.data.append(sample)

	def precalculate_conv(self, frcnn):
		assert self.image_set == "train", "[!] Precalculating only implemented for train set not for: {}".format(self.image_set)
		self.prec_conv = True
		prec = {}
		for seq in self._train_folders:
			print("[*] Precalcuating conv of {}".format(seq))
			d = MOT_Sequence(seq)
			for sample in d:
				c = frcnn.get_net_conv(torch.from_numpy(sample['data']), torch.from_numpy(sample['im_info']))
				prec[sample['im_path']] = {'conv':c, 'im_info':sample['im_info']}

		self.prec_data = prec



	def __len__(self):
		return len(self._dataloader.data)

	def __getitem__(self, idx):
		"""Return the ith Object"""
		if self.prec_conv:
			track = self._dataloader.data[idx]
			res = []
			# construct image blobs and return new list, so blobs are not saved into this class
			for f in track:
				prec = self.prec_data[f['im_path']]
				sample = {}
				sample['id'] = f['id']
				sample['im_path'] = f['im_path']
				sample['conv'] = prec['conv']
				sample['im_info'] = prec['im_info']
				if 'gt' in f.keys():
					sample['gt'] = f['gt'] * sample['im_info'][2]
				sample['active'] = f['active']
				sample['vis'] = f['vis']

				res.append(sample)
			return res
		else:
			return self._dataloader[idx]
