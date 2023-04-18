# =============================================================================
# Copyright 2022-2023. Codex Laboratories LLC. All rights reserved.
#
# Created By: Tyler Fedrizzi
# Created On: 3 April 2023
#
#
# Description: Utilities to run with PyTorch tools
# =============================================================================
try:
    from torch import Tensor
except ModuleNotFoundError:
    print("Please install PyTorch Version 2.0 or greater")

from pandas import DataFrame


class TorchModelBase():
    """
    Base Custom Torch module that describes the required methods that
    need to be implemented by the User so that they can run their
    models in the normalized setup.

    # You can inherit from the class to create your Algorithm that will
    # run in the SWARM System

    ### Arguments:
    - None
    """
    def __init__(self, parameters: dict, detection: bool = True, classification: bool = True) -> None:
        # This should be initalized as the Class that you wish to
        # make that describes the network. So if you created a class
        # called DetectNet, then this would be:
        # Inputing your parameters using ** allows you to set your 
        # parameters as input.
        # self.network = DetectNet(**parameters)
        self.network = None
        self.detection = detection
        self.classification = classification
        self.segmentation = False  # TODO

        # Example output dataframe. Add rows using the following:
        if detection and classification:
            # xmin, ymin are the Top Left coordinates of the bounding box in pixel coordinates
            # xmax, ymax are the bottom Right coordinates of the bounding box
            # confidence is a float in the range [0.0, 1.0]
            # name is the class label
            self.required_columns = ["xmin", "ymin", "xmax", "ymax", "confidence", "name"]
        elif detection and not classification:
            self.required_columns = ["confidence", "name"]
        # Below is the fastest way to add a dataframe together
        # https://stackoverflow.com/questions/24284342/insert-a-row-to-pandas-dataframe
        #  df = pd.concat([pd.DataFrame([[1,2]], columns=df.columns), df], ignore_index=True)
        self.output_dataframe = DataFrame(columns=self.required_columns)

    def preprocess_images(self, images: list, **kwargs) -> list:
        """
        Pre-process the provided images, which will always be a numpy
        array that is of dimension (Height, Width, Number of Channels).
        The goal of this method is to pre-process the image such that

        
        ### Inputs:
        - images [list] A list of images with Numpy

        ### Output:
        - A list of transformed images
        """
        raise NotImplementedError()

    def postprocess_output(self, network_output: Tensor) -> DataFrame:
        """
        Postprocess the output tensor of the model, generating a Pandas
        DataFrame that can be passed to the Detection building module
        and provide detections to the system.

        ### Input:
        - network_output [Tensor] The output Tensor of the Model

        ### Output:
        - A Pandas DataFrame containing all required metadata as listed
          in the PyTorch documentation on the SWARM Website
        """
        raise NotImplementedError("Implement the post Processing!")