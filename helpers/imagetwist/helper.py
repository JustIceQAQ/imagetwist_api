import os
import secrets
import string
from enum import Enum
from typing import Optional
from bs4 import BeautifulSoup

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Origin": "https://imagetwist.com"
}


class ImageTwistDomainEnum(str, Enum):
    imagetwist_com = "imagetwist.com"


class ImageTwistHelper:
    def __init__(self, account: str, password: str):
        self.session = httpx.Client(timeout=300)
        self.account = account
        self.password = password
        self.session.headers.update(HEADERS)
        self.base_url = "https://imagetwist.com/"
        self.cookie_status = None

    def _get_status_url(
            self,
            uid: str,
            image_name: str,
            domain: ImageTwistDomainEnum
    ) -> str:
        return f"https://s10.imagetwist.com/tmp/status.html?{uid}={image_name}=https://{str(domain)}/"

    def _get_upload_url(self, uid: str) -> str:
        return (f"https://img400.imagetwist.com/cgi-bin/upload.cgi?"
                f"upload_id={uid}&js_on=1&utype=reg&upload_type=url")

    def _get_upload_data(
            self,
            sess_id: str,
            image_url: str,
            domain: ImageTwistDomainEnum) -> dict:
        return {
            "sess_id": sess_id,
            "upload_type": "url",
            "mass_upload": "1",
            "url_mass": image_url,
            "thumb_size": "170x170",
            "per_row": "1",
            "sdomain": str(domain),
            "fld_id": "0",
            "tos": "1",
            "submit_btn": "Upload",
        }

    def _get_upload_success_data(self, fn: str) -> dict:
        return {"fn": fn, "st": "OK", "op": "upload_result", "per_row": "1"}

    def login_status(self, show_message: bool = True):
        if self.cookie_status is not None:
            if show_message:
                print("imagetwist.com login success")
            return None
        raise ValueError("imagetwist.com login failed")

    def _get_sess_id(self) -> str:
        self.login_status(show_message=False)
        return self.cookie_status.get("xfss")

    def login(self):
        response = self.session.post(
            self.base_url,
            data={"op": "login", "login": self.account, "password": self.password, "submit_btn": "Login"}
        )
        if response.is_success or response.is_redirect:
            self.cookie_status = response.cookies
            return self.login_status()
        raise ValueError("imagetwist.com login failed")

    def upload_image_from_url(
            self,
            image_url: str,
            domain: Optional[ImageTwistDomainEnum] = ImageTwistDomainEnum.imagetwist_com
    ) -> Optional[str]:
        runtime_uid = self.get_ramdom_uid()
        image_name = os.path.basename(image_url)
        status_url = self._get_status_url(runtime_uid, image_name, domain)
        status_response = self.session.get(status_url)
        if not status_response.is_success:
            return None

        upload_url = self._get_upload_url(runtime_uid)
        sess_id = self._get_sess_id()
        upload_data = self._get_upload_data(sess_id, image_url, domain)
        upload_response = self.session.post(upload_url, data=upload_data)
        if not upload_response.is_success:
            return None

        parsed_upload_response = BeautifulSoup(upload_response.text, "html.parser")

        fn_value = parsed_upload_response.find("textarea", {"name": "fn"}).text
        st_value = parsed_upload_response.find("textarea", {"name": "st"}).text
        if st_value != "OK":
            return None

        upload_success_data = self._get_upload_success_data(fn_value)
        upload_success_response = self.session.post(self.base_url, data=upload_success_data)
        if not upload_success_response.is_success:
            return None
        parsed_upload_success_response = BeautifulSoup(upload_success_response.text, "html.parser")
        with open("output1.html", "w") as file:
            file.write(str(parsed_upload_success_response))

        self.parsed_to_image_info(parsed_upload_success_response)

    def parsed_to_image_info(self, parsed_upload_success_response: BeautifulSoup) -> dict:
        image_data = {}
        image_info = parsed_upload_success_response.select_one("div.image_info > div.linkus")
        titles = image_info.select("div.col-sm-4")
        values = image_info.select("div.col-sm-8")
        for title, value in zip(titles, values):
            title_text = title.get_text()

            if (value.attrs is not None) and ((value_class := value.attrs.get("class", None)) is not None):
                if 'blue-bolded' in value_class:
                    image_data[title_text.strip()] = value.text.strip()
                    continue
            if (value_input := value.find("input")) is not None:
                image_data[title_text.strip()] = value_input.get('value')
                continue
            if (value_image := value.find("img")) is not None:
                image_data[title_text.strip()] = value_image.get('src')
                continue
        image_data["Preview Full"] = image_data["Preview"].replace("/th/", "/i/")
        return image_data

    def get_ramdom_uid(self) -> str:
        return "".join(secrets.choice(string.digits) for _ in range(12))
