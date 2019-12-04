# kb-agent_4th
## About

KB-Agnet: Interactive Learning through dialog between bot and user.  
It recognizes current dialog's topic, and asks unknown knowledge to user.  
Then, receiving user's answer, it expands its KB.  

## prerequisite
* `python 3`

## Set up
```
pip install -r requirements.txt
```

## How to run
* API ver
```
python chat_api.py
```
Input/Output

| Key | Input Value | Output Value |
|----|-------------|-------------|
|user_id | 사용자별 고유 식별자(string) | 사용자별 고유 식별자(string) |
|utterance | 사용자 발화 문장(string) | 시스템 발화 문장(string) |
|frames | 이전 Output Value와 동일(최초 대화시에는 빈 리스트) | 인식된 frame 리스트 |
|entities | 이전 Output Value와 동일(최초 대화시에는 빈 리스트) | 인식된 entity 리스트 |
|q_list | 이전 Output Value와 동일(최초 대화시에는 빈 리스트) | 인식된 frame 혹은 enitity에 대한 질문 리스트 |
|knowledge | 이전 Output Value와 동일(최초 대화시에는 빈 리스트) | 사용자로부터 습득한 지식 리스트 |


## Mailing List
`asm427@kaist.ac.kr`  


## Acknowledgement
This work was supported by Institute of Information & Communications Technology Planning & Evaluation (IITP) grant funded by the Korea government(MSIT) [2016-0-00562(R0124-16-0002), Emotional Intelligence Technology to Infer Human Emotion and Carry on Dialogue Accordingly]
