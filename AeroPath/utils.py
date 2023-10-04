import nibabel as nib
import numpy as np
from nibabel.processing import resample_to_output
from skimage.measure import marching_cubes


def load_ct_to_numpy(data_path):
    if type(data_path) != str:
        data_path = data_path.name

    image = nib.load(data_path)
    resampled = resample_to_output(image, None, order=0)
    data = resampled.get_fdata()

    data = np.rot90(data, k=1, axes=(0, 1))

    data[data < -1024] = -1024
    data[data > 1024] = 1024

    data = data - np.amin(data)
    data = data / np.amax(data) * 255
    data = data.astype("uint8")

    print(data.shape)
    return [data[..., i] for i in range(data.shape[-1])]


def load_pred_volume_to_numpy(data_path):
    if type(data_path) != str:
        data_path = data_path.name

    image = nib.load(data_path)
    resampled = resample_to_output(image, None, order=0)
    data = resampled.get_fdata()

    data = np.rot90(data, k=1, axes=(0, 1))

    data[data > 0] = 1
    data = data.astype("uint8")

    print(data.shape)
    return [data[..., i] for i in range(data.shape[-1])]


def nifti_to_glb(path, output="prediction.obj"):
    # load NIFTI into numpy array
    image = nib.load(path)
    resampled = resample_to_output(image, [1, 1, 1], order=1)
    data = resampled.get_fdata().astype("uint8")

    # extract surface
    verts, faces, normals, values = marching_cubes(data, 0)
    faces += 1

    with open(output, "w") as thefile:
        for item in verts:
            thefile.write("v {0} {1} {2}\n".format(item[0], item[1], item[2]))

        for item in normals:
            thefile.write("vn {0} {1} {2}\n".format(item[0], item[1], item[2]))

        for item in faces:
            thefile.write(
                "f {0}//{0} {1}//{1} {2}//{2}\n".format(
                    item[0], item[1], item[2]
                )
            )