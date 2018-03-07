# docker-duply
A duply base image of alpine:3.7 containing duplicity and duply

## Tags
- `0.7.17-2.0.4` (  [0.7.17-2.0.4/Dockerfile](https://github.com/enonic-cloud/docker-duply/blob/master/0.7.17-2.0.4/Dockerfile) ). Contains duplicity version 0.7.17 and duply version 2.0.4.



## Usage
Use this image as a base for your duply backup container. You can either clone/fork the repository `https://github.com/enonic-cloud/docker-duply.git` or use `enoniccloud/duply:<version>|latest` in your `FROM` tag.
```
FROM enoniccloud/duply:0.7.17-2.0.4
ADD your_backup_profile /etc/duply/profile
CMD duply profile backup
```
