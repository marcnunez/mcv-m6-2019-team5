from model import Video


def main():
    # TODO

    video = Video("../datasets/AICity_data/train/S03/c010/vdo.avi",
                  "../datasets/AICity_data/train/S03/c010/Anotation_40secs_AICITY_S03_C010.xml")

    for im, f in video.get_frames():
        print(im.shape, f.id)


if __name__ == '__main__':
    main()