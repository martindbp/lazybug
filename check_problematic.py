from wrapped_json import json

examples = {
    'youtube-YtzqsA-a8MM': [  # doutinghao 1
        ('13:46.0', 'ting3de5zhu4'),
        ('26:32.5', 'hu2shuo1ba1dao4 was wrong'),
        ('13:05.5', 'chu1zu1 was separated'),
        ('13:08.0', 'cai2 da3dao4 was wrong'),
    ],
    'youtube-8b0TGFqHJ4E': [  # doutinghao 2
        ('1:17.5', 'fix name'),
        ('20:38.5', 'passbook, problem with gen1+ti2'),
        ('21:51.5', 'chang2bei4 was wrong'),
        ('22:01.5', 'should be ok ok'),
        ('22:18.9', 'dang1 should be managed'),
        ('33:20.5', 'huan2'),
        ('33:27.0', 'bu4dei3'),
        ('37:47.0', 'guo'),
        ('39:18.0', 'yue1'),
        ('39:58.0', 'problem with gen1'),
        ('40:41.0', 'hard should be sad'),
        ('40:35.5', 'ma1bai2 wrong segmentation'),
    ],
    'youtube-OiP9UIZ9r5A': [  # doutinghao 3
        ('3:4.5', 'chu1qian2 should not be MW'),
        ('8:29.0', 'de2hen3'),
        ('8:38.5', 'hui2shi4'),
        ('8:44.5', 'missing word'),
        ('11:35.0', 'le5'),
        ('12:31.0', 'guan = off'),
        ('12:42.0', 'weird pinyin'),
        ('12:49.5', 'huan2gei3 wrong translation'),
        ('14:02.5', 'han2shu3jia4 translation contains other part of sentence, also missing pinyin'),
        ('20:45.0', '毕了业'),
        ('21:28.5', 'missing pinyin'),
        ('21:32.0', 'should be guo4'),
        ('34:09.5', 'le5bie2'),
    ],
}


for video_id, timings in examples.items():
    print('Video', video_id, '\n')
    with open(f'data/remote/public/subtitles/{video_id}.json') as f:
        data = json.load(f)

    example_timings = []
    for timing, note in timings:
        minutes, seconds = timing.split(':')
        minutes = int(minutes)
        seconds = float(seconds)
        example_timings.append((seconds + 60*minutes, note))

    lines = data['lines']
    for line in lines:
        for i in range(len(line[0])):
            t0 = line[1][i]
            t1 = line[2][i]
            for timing, note in example_timings:
                if t0 <= timing <= t1:
                    print(' '.join(line[0]), note)
                    words = line[-1]
                    for (_, _, hz, py, tr) in words:
                        print('\t', hz, py, tr)
    print('')
