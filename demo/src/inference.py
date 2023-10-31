import configparser
import logging
import os
import shutil
import traceback


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
        rads_config.set(
            "System",
            "pipeline_filename",
            os.path.join(model_path, task, "pipeline.json"),
        )
        rads_config.add_section("Runtime")
        rads_config.set(
            "Runtime", "reconstruction_method", "thresholding"
        )  # thresholding, probabilities
        rads_config.set("Runtime", "reconstruction_order", "resample_first")
        rads_config.set("Runtime", "use_preprocessed_data", "False")

        with open("rads_config.ini", "w") as f:
            rads_config.write(f)

        # finally, run inference
        from raidionicsrads.compute import run_rads

        run_rads(config_filename="rads_config.ini")

        # rename and move final result
        os.rename(
            "./result/prediction-"
            + splits[0]
            + "/T0/"
            + splits[0]
            + "-t1gd_annotation-"
            + name
            + ".nii.gz",
            "./prediction.nii.gz",
        )
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
