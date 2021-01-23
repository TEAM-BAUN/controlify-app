import redis

# * ______________Redis Baglantisi______________
def redisServerSetup():
    """
    [
    ! Canli veri alisverisini saglayabilen (pubsub)
    ! ayni zamanda NoSQL gibi calisan, key:value seklinde ram hafizasinda veri saklayabilen bir database
    ]
    """
    try:
        # r = redis.Redis("localhost")
        # r = redis.Redis(
        #     host="redis-11907.c135.eu-central-1-1.ec2.cloud.redislabs.com",
        #     password="jPHWcbukgy7r1qmBwa9VxNRHZmfeD9N9",
        #     port=11907,
        #     db=0,
        # )
        r = redis.Redis(
            host="redis-19465.c135.eu-central-1-1.ec2.cloud.redislabs.com",
            password="RQ1k6C31YkC4S2I1BhMRIq4pBB0udLjB",
            port=19465,
            db=0,
        )
        p = r.pubsub(ignore_subscribe_messages=True)

        # ? Requsts yani (logs)kayitlar kanalina abone olduk burda tum cihazlarin yapmak istedikleri islemlerin trafigini logluyacagiz
        # ? Buna gore clientlari uyaracagiz hali hazirda baglanti durumunda olan clientlara baglanti istegi gonderilmesini engelliyecegiz
        return (True, r, p)
    except:
        return (False, None, None)