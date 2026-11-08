#!/usr/bin/env bash
#
# Build a postmarketOS rootfs image for hanoip, without pmbootstrap.
#
#   apk.static installs alpine-base + postmarketos-base (Alpine edge + the
#   postmarketOS "Nura" repo) into a directory, we configure it (hostname,
#   passwords, boot banner, a USB CDC-ECM gadget so we can ssh in over the USB
#   cable), then pack it into an ext4 image and xz-compress it.
#
#   scripts/build-rootfs.sh            -> out/rootfs-hanoip.img.xz
#
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
CONT="${CONT:-hanoip-build}"
OUT="${1:-$HERE/out/rootfs-hanoip.img}"
PUBKEY="${SSH_PUBKEY:-$HOME/.ssh/id_ed25519.pub}"

# Optional: an SSH public key to authorise for root/user, so we can log in over
# the USB network without a password prompt.
if [ -f "$PUBKEY" ]; then
	docker cp "$PUBKEY" "$CONT:/tmp/hanoip_authorized_keys" >/dev/null
	echo ">> embedding ssh key $PUBKEY"
fi

docker exec -i "$CONT" bash -s <<'EOS'
set -e

# --- apk.static (Alpine's static package manager) ---
APK=/root/apk/apk.static
if [ ! -x "$APK" ]; then
	mkdir -p /root/apk && cd /root/apk
	curl -sS -o apk-tools-static.apk \
		https://dl-cdn.alpinelinux.org/alpine/edge/main/aarch64/apk-tools-static-3.0.9-r0.apk
	tar -xzf apk-tools-static.apk sbin/apk.static
	mv sbin/apk.static apk.static
	chmod +x apk.static
fi

R=/root/rootfs
rm -rf "$R"
mkdir -p "$R/etc/apk"
cat > "$R/etc/apk/repositories" <<EOF
https://dl-cdn.alpinelinux.org/alpine/edge/main
https://dl-cdn.alpinelinux.org/alpine/edge/community
https://mirror.postmarketos.org/postmarketos/master
EOF

echo ">> installing packages"
"$APK" --arch aarch64 --root "$R" --initdb --allow-untrusted --update-cache \
	add alpine-base postmarketos-base openssh-server

# --- configuration ---
echo hanoip > "$R/etc/hostname"

# root + user passwords (postmarketOS convention: 147147)
chroot "$R" /bin/sh -c 'echo root:147147 | chpasswd'
chroot "$R" /bin/sh -c \
	'adduser -D -s /bin/ash user; echo user:147147 | chpasswd; addgroup user wheel' \
	|| echo "  (user account setup reported an error)"

# Allow password ssh login as root (bring-up convenience).
echo "PermitRootLogin yes" >> "$R/etc/ssh/sshd_config"

# Authorise the host's ssh key for root and user, if one was provided.
if [ -f /tmp/hanoip_authorized_keys ]; then
	for home in /root /home/user; do
		mkdir -p "$R$home/.ssh"
		cp /tmp/hanoip_authorized_keys "$R$home/.ssh/authorized_keys"
		chmod 700 "$R$home/.ssh"
		chmod 600 "$R$home/.ssh/authorized_keys"
	done
	chown -R 1000:1000 "$R/home/user/.ssh"
fi

# Serial console over the USB CDC-ACM gadget (macOS: /dev/tty.usbmodem*).
# A byte stream avoids the ECM/TCP data-path problems entirely.
echo 'ttyGS0::respawn:/sbin/getty -L 115200 ttyGS0 vt100' >> "$R/etc/inittab"

# USB network: DHCP server so the host auto-configures (no sudo needed there).
# The fork's default (172.16.41.1) is a different subnet from the client, so pin
# both ends to 172.16.42.x.
cat > "$R/etc/conf.d/unudhcpd" <<'EOF'
UNUDHCPD_SERVER=172.16.42.1
UNUDHCPD_CLIENT=172.16.42.2
EOF

# Banner once userspace is up (runs from /etc/local.d via the `local` service).
mkdir -p "$R/etc/local.d"
cat > "$R/etc/local.d/hanoip-banner.start" <<'EOF'
#!/bin/sh
echo
echo "========= hanoip: postmarketOS userspace is UP ========="
uname -a
echo "rootfs: $(grep " / " /proc/mounts | cut -d" " -f1)"
echo "usb0:   $(ifconfig usb0 2>/dev/null | grep -o 'inet addr:[0-9.]*' | head -1)"
echo "======================================================="
EOF
chmod +x "$R/etc/local.d/hanoip-banner.start"

# --- USB CDC-ECM gadget (macOS speaks CDC-ECM natively) ---
cat > "$R/etc/init.d/usb-gadget" <<'EOF'
#!/sbin/openrc-run
description="USB CDC-ECM gadget (network over the USB cable)"

depend() {
	need localmount
	before unudhcpd.usb0 networking
}

start() {
	ebegin "Creating USB CDC-ECM gadget"
	mountpoint -q /sys/kernel/config || mount -t configfs none /sys/kernel/config 2>/dev/null
	G=/sys/kernel/config/usb_gadget/g1
	mkdir -p "$G"
	echo 0x18d1 > "$G/idVendor"
	echo 0xd001 > "$G/idProduct"
	mkdir -p "$G/strings/0x409"
	echo "Motorola" > "$G/strings/0x409/manufacturer"
	echo "hanoip" > "$G/strings/0x409/serialnumber"
	echo "Moto G40 Fusion (postmarketOS)" > "$G/strings/0x409/product"
	mkdir -p "$G/functions/ecm.usb0"
	mkdir -p "$G/configs/c.1/strings/0x409"
	echo "CDC-ECM" > "$G/configs/c.1/strings/0x409/configuration"
	ln -sf "$G/functions/ecm.usb0" "$G/configs/c.1/" 2>/dev/null
	udc="$(ls /sys/class/udc 2>/dev/null)"
	if [ -z "$udc" ]; then
		eerror "no USB Device Controller (UDC); is usb_1_dwc3 dr_mode=peripheral?"
		return 1
	fi
	echo "$udc" > "$G/UDC"

	# Static point-to-point link: device 172.16.42.1, host 172.16.42.2.
	i=0
	while [ ! -e /sys/class/net/usb0 ] && [ $i -lt 50 ]; do sleep 0.1; i=$((i+1)); done
	ifconfig usb0 172.16.42.1 netmask 255.255.255.0 up
	eend $?
}
EOF
chmod +x "$R/etc/init.d/usb-gadget"
ln -sf /etc/init.d/usb-gadget "$R/etc/runlevels/boot/usb-gadget"
# unudhcpd.usb0 (postmarketos-base default) serves DHCP on usb0 to the host
ln -sf /etc/init.d/unudhcpd.usb0 "$R/etc/runlevels/boot/unudhcpd.usb0"

# --- pack ---
echo ">> packing ext4 image"
cd /root
rm -f rootfs.img rootfs.img.xz
truncate -s 2G rootfs.img
mke2fs -q -t ext4 -d "$R" -L pmOS_root -F rootfs.img
xz -T0 -9 -f -k rootfs.img
ls -la rootfs.img rootfs.img.xz
EOS

docker cp "$CONT:/root/rootfs.img.xz" "$OUT.xz"
ls -la "$OUT.xz"
