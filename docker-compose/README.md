# docker-compose

---

### How to run

1. Clone repo locally
2. Go to local repo
3. Type `docker-compose build`
4. Type `docker-compose up` if you want to see output in console, otherwise `docker-compose up -d`
5. Go to `localhost:5000` and enjoy!

---

### Docker structure

##### Web

Uses Python:3.8 image and Flask framework in order to provide light and fast local web server with bootstrap-based frontend

**Accessible under** `localhost:5000`

##### Worker

Celery worker made to run and maintain background task, such as learning agent and providing updated status

##### Redis

Cache backend used to store Celery task ids

##### Devnetwork

Network created inside Docker container to allow services to communicate with eachoter, giving us fully functional project

---

### Development

For every celery-related (task) change, container needs to be reloaded. Flask auto reloads itself upon code change.

> :warning: **Each container start-up terminates all previous tasks**
