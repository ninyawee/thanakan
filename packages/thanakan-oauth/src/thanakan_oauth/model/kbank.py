from typing import Optional

from loguru import logger
from pydantic import model_validator
from thanakan_oauth.model.common import APIModel, SlipData


class KbankSlipVerifyResponse(APIModel):

    rqUID: str
    status_code: str
    status_message: str
    data: Optional[SlipData]

    @property
    def status(self):
        return f"{self.status_code}: {self.status_message}"

    @model_validator(mode="before")
    @classmethod
    def fail_make_data_none(cls, values):
        """
        This is to prevent expected consequnece validations fail in the `SlipData` .
        """
        if values["statusCode"] != "0000":
            logger.warning(
                "request not success, with Error {}: {}",
                values["statusCode"],
                values["statusMessage"],
            )
            logger.debug("This is data. {}", values["data"])
            values["data"] = None
        return values
