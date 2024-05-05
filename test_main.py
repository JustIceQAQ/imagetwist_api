from bs4 import BeautifulSoup


def test_main():
    image_data = {}

    with open("output1.html", "r") as file:
        data = BeautifulSoup(file.read(), "html.parser")
    image_info = data.select_one("div.image_info > div.linkus")
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
