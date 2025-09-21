




class Config:
    # 线下比赛时根据实际抓包修改
    flag_endpoint = "/slab-match/api/v1/player/answer-panel/answer"
    flag_ip = "192.168.127.12"
    auth_headers = {
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vdXNlcjoxMjE1L3JhbmdlLXVzZXIvYXBpL2lubmVyL2F1dGgiLCJpYXQiOjE3NTgyNDkwNTQsImV4cCI6MTc1ODQ2NzE5MywibmJmIjoxNzU4MjUxMTkzLCJqdGkiOiJLQk56OHd2d3F5YXMxQVZyIiwic3ViIjoxNjQ1LCJwcnYiOiIzN2I3YzUwYjI1MDQxYTRjMjBmZTQ3YzI0MmUxYmZkMGY2MzA5MmM1Iiwic2xhYi1tYXRjaF8yNyI6MTY0NSwibG9naW5fdG9rZW4iOiJiMWJhOTgzNGE3MDVhNjY4MDFjYzBlYmY5MmJkZTg5MyIsImd1YXJkIjoicGxheWVyIiwidXNlcm5hbWUiOiJ5bF8xMzcifQ.PNUqSK0zzq1LX8l_NebQRRWreOD_ce_AYIfUGUxJ5Yc',
    }

    subject = [
        {"name": "FXCM", "matchId": "ufky3d"},
        {"name": "tq", "matchId": "ufky4d"},
    ]
    
    flag_info = [
        {"part": "base", "exerciseId": {"hdp": "d", "default": 290}},
        {"part": "once", "flag": {"hdp": "hd"}},
        {"part": "once", "matchId": {"hdp": "hd"}}
    ]
    
    
    
    
    
    
    
    
    
    
