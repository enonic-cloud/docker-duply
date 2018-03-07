# docker-duply
A duply base image of alpine:3.7 containing duplicity 0.7.17 and duply 2.0.4

Use this image as a base for your duply backup container. You can either clone/fork the repository `https://github.com/enonic-cloud/docker-duply.git` or use `enoniccloud/duply:<version>|latest` in your `FROM` tag.

Example:
```
FROM enoniccloud/duply:0.7.17-2.0.4
ADD your_backup_profile /etc/duply/profile
CMD duply profile backup
```
