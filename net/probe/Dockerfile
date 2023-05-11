# install binary from linux image
FROM debian:latest as debian
RUN apt-get update && apt-get install hping3 -y

# Use busybox as the base image
FROM busybox
# Copy hping3
COPY --from=debian /usr/sbin/hping3 /bin/hping3 
# Copy hping3 dependencies
COPY --from=debian /usr/lib/x86_64-linux-gnu/libpcap.so.0.8 \
                   /usr/lib/x86_64-linux-gnu/libtcl8.6.so \
                   /lib/x86_64-linux-gnu/libdbus-1.so.3 \
                   /lib/x86_64-linux-gnu/libdl.so.2 \
                   /lib/x86_64-linux-gnu/libz.so.1 \
                   /lib/x86_64-linux-gnu/libm.so.6 \
                   /usr/lib/x86_64-linux-gnu/libsystemd.so.0 \
                   /lib/x86_64-linux-gnu/librt.so.1 \
                   /lib/x86_64-linux-gnu/liblzma.so.5 \
                   /usr/lib/x86_64-linux-gnu/libzstd.so.1 \
                   /usr/lib/x86_64-linux-gnu/liblz4.so.1 \
                   /usr/lib/x86_64-linux-gnu/libgcrypt.so.20 \
                   /lib/x86_64-linux-gnu/libgpg-error.so.0 \
                   /lib/  
# Copy server file
COPY ./server /home/

# Run server file
CMD /home/server