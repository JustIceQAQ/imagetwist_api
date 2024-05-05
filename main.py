from helpers.imagetwist.helper import ImageTwistHelper

if __name__ == '__main__':
    ith = ImageTwistHelper(account="<ACCOUNT>", password="<PASSWORD>")
    ith.login()
    ith.upload_image_from_url("<IMAGE URL>")

