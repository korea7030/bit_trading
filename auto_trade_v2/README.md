## 1. Oracle Cloud 가입 및 세팅
https://technfin.tistory.com/entry/%EC%98%A4%EB%9D%BC%ED%81%B4-%ED%81%B4%EB%9D%BC%EC%9A%B0%EB%93%9C-%EB%AC%B4%EB%A3%8C-%EA%B0%80%EC%9E%85-%EC%98%A4%EB%A5%98-%EB%B0%8F-%EC%A3%BC%EC%9D%98%EC%82%AC%ED%95%AD

https://technfin.tistory.com/entry/%EC%98%A4%EB%9D%BC%ED%81%B4-%ED%81%B4%EB%9D%BC%EC%9A%B0%EB%93%9C-%EC%9D%B8%EC%8A%A4%ED%84%B4%EC%8A%A4-%EC%83%9D%EC%84%B1-%EC%84%9C%EB%B2%84-%EB%A7%8C%EB%93%A4%EA%B8%B0

#### mac에서 Oracle Cloud 접속방법
```
cd {key파일 경로} && ssh -i {keyfile명} opc@{Oracle Instance Public IP}
```

## 2. Linux 서버 시간 설정(한국시간으로 변경)
https://technfin.tistory.com/entry/%EB%A6%AC%EB%88%85%EC%8A%A4-%EC%84%9C%EB%B2%84%EC%8B%9C%EA%B0%84-%EB%B0%8F-%ED%83%80%EC%9E%84%EC%A1%B4-%ED%99%95%EC%9D%B8-%EB%B0%8F-%EB%B3%80%EA%B2%BD%ED%95%98%EA%B8%B0 


### 2.1 디렉토리 생성(이미 생성되어있는 directory는 skip해도 됨)
```
mkdir cron
mkdir logs
mkdir trade_bot
```

### 2.2 파일 업로드
#### 2.2.1 trade_bot 에 올릴 파일
5m3t_only_buy_bot.py <br>
5m3t_only_sell_bot.py <br>
monitoring.py

### 2.3 프로그램 수행 용 쉘 스크립트 작성하기
#### 파일위치 및 파일명 : /home/opc/cron/monitoring.sh

```sh
#!/bin/sh
export PATH=$PATH:/usr/local/bin
 
# Change Directory
cd /home/opc/
 
# Run Program
python ./trade_bot/monitoring.py I >> /home/opc/logs/monitoring.log 2>&1
```

### 2.4 crontab 등록(모니터링 shell만 해당)
```sh
crontab -e
```
```sh
# Monitoring Process - every 1 mins
*/1 * * * * /home/opc/cron/pid_monitoring.sh >> /home/opc/logs/pid_monitoring.log 2>&1
```
#### crontab 실행유무 확인
```sh
cd logs
ls -rlt  # logs이동 후 명령어 실행 시, monitoring.log 파일이 생기면 성공
```

## 2.5 5분봉 3틱 실행(매수/매도)
```sh
cd trade_bot
# 매수
nohup python -u 5m3t_only_buy_bot.py I 10000 >> /home/opc/logs/5m3t_only_buy_bot.log &
# 매도
nohup python -u 5m3t_only_sell_bot.py I 1 >> /home/opc/logs/5m3t_only_sell_bot.log &
```

#### 파이썬 코드 실행확인 방법
```sh
ps -ef | grep py  # 실행
```
#### 조회결과
#### buy_bot.py, sell_bot.py, monitoring.py 이 3가지가 아래처럼 떠 있으면 성공
```sh
root        1499       1  0  4월25 ?      00:00:00 /usr/libexec/platform-python -s /usr/sbin/firewalld --nofork --nopid
root        1584       1  0  4월25 ?      00:01:57 /usr/libexec/platform-python -Es /usr/sbin/tuned -l -P
opc       855840       1 20  5월11 ?      23:20:59 python -u 5m3t_only_sell_bot.py I 1
opc       856062       1 20  5월11 ?      23:06:46 python -u 5m3t_only_buy_bot.py I 10000
opc       974740  974739  6  5월12 ?      06:49:38 python ./trade_bot/monitoring.py I
opc      2308049 2302634  0 07:47 pts/0    00:00:00 grep --color=auto py
```

## 3. 로그 정리 방법
### 아래 사이트 보고 참고하되, 세팅시 폴더명 주의(python 이 아님. opc임)
https://technfin.tistory.com/entry/%EB%A6%AC%EB%88%85%EC%8A%A4-%EB%A1%9C%EA%B7%B8-%EA%B4%80%EB%A6%AC%ED%95%98%EA%B8%B0-logrotate
