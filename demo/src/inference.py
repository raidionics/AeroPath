import configparser
import logging
import os
import shutil
import traceback
import json
import fnmatch


def run_model(
    input_path: str,
    model_path: str,
    verbose: str = "info",
    task: str = "CT_Airways",
    name: str = "Airways",
):
    if verbose == "debug":
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose == "info":
        logging.getLogger().setLevel(logging.INFO)
    elif verbose == "error":
        logging.getLogger().setLevel(logging.ERROR)
    else:
        raise ValueError("Unsupported verbose value provided:", verbose)

    # delete patient/result folder if they exist
    if os.path.exists("./patient/"):
        shutil.rmtree("./patient/")
    if os.path.exists("./result/"):
        shutil.rmtree("./result/")

    patient_directory = ""
    output_path = ""
    try:
        # setup temporary patient directory
        filename = input_path.split("/")[-1]
        splits = filename.split(".")
        extension = ".".join(splits[1:])
        patient_directory = "./patient/"
        os.makedirs(patient_directory + "T0/", exist_ok=True)
        shutil.copy(
            input_path,
            patient_directory + "T0/" + splits[0] + "-t1gd." + extension,
        )

        # define output directory to save results
        output_path = "./result/prediction-" + splits[0] + "/"
        os.makedirs(output_path, exist_ok=True)

        # Setting up the configuration file
        rads_config = configparser.ConfigParser()
        rads_config.add_section("Default")
        rads_config.set("Default", "task", "mediastinum_diagnosis")
        rads_config.set("Default", "caller", "")
        rads_config.add_section("System")
        rads_config.set("System", "gpu_id", "-1")
        rads_config.set("System", "input_folder", patient_directory)
        rads_config.set("System", "output_folder", output_path)
        rads_config.set("System", "model_folder", model_path)
        rads_config.set('System', 'pipeline_filename', os.path.join(output_path,
                                                                    'test_pipeline.json'))
        rads_config.add_section("Runtime")
        rads_config.set("Runtime", "reconstruction_method", "thresholding")  # thresholding, probabilities
        rads_config.set("Runtime", "reconstruction_order", "resample_first")
        rads_config.set("Runtime", "use_preprocessed_data", "False")

        with open("rads_config.ini", "w") as f:
            rads_config.write(f)

        pip = {}
        step_index = 1
        pip_num = str(step_index)
        pip[pip_num] = {}
        pip[pip_num]["task"] = "Classification"
        pip[pip_num]["inputs"] = {}  # Empty input means running it on all existing data for the patient
        pip[pip_num]["target"] = ["MRSequence"]
        pip[pip_num]["model"] = "MRI_SequenceClassifier"
        pip[pip_num]["description"] = "Classification of the MRI sequence type for all input scans."

        step_index = step_index + 1
        pip_num = str(step_index)
        pip[pip_num] = {}
        pip[pip_num]["task"] = 'Model selection'
        pip[pip_num]["model"] = task
        pip[pip_num]["timestamp"] = 0
        pip[pip_num]["format"] = "thresholding"
        pip[pip_num]["description"] = f"Identifying the best {task} segmentation model for existing inputs"

        with open(os.path.join(output_path, 'test_pipeline.json'), 'w', newline='\n') as outfile:
            json.dump(pip, outfile, indent=4, sort_keys=True)

        # finally, run inference
        from raidionicsrads.compute import run_rads
        run_rads(config_filename="rads_config.ini")

        logging.info(f"Looking for the following pattern: {task}")
        patterns = [f"*-{name}.*"]
        existing_files = os.listdir(os.path.join(output_path, "T0"))
        logging.info(f"Existing files: {existing_files}")
        fileName = str(os.path.join(output_path, "T0",
                                    [x for x in existing_files if
                                     any(fnmatch.fnmatch(x, pattern) for pattern in patterns)][0]))
        os.rename(src=fileName, dst="./prediction.nii.gz")

        # Clean-up
        if os.path.exists(patient_directory):
            shutil.rmtree(patient_directory)
        if os.path.exists(output_path):
            shutil.rmtree(output_path)

    except Exception:
        print(traceback.format_exc())
        # Clean-up
        if os.path.exists(patient_directory):
            shutil.rmtree(patient_directory)
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
