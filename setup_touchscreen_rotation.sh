#!/bin/bash

echo "🔁 Setting display rotation in /boot/config.txt..."
# Ensure the correct rotation setting is added
sudo sed -i '/^display_lcd_rotate=/d' /boot/config.txt
echo "display_lcd_rotate=2" | sudo tee -a /boot/config.txt

echo "✅ Display rotation set to 180°."

# Ensure you're using X11 (legacy session)
LIGHTDM_CONF="/etc/lightdm/lightdm.conf"
echo "🛠️ Setting default session to X11 in $LIGHTDM_CONF..."
if ! grep -q "user-session=" "$LIGHTDM_CONF"; then
    echo -e "[Seat:*]\nuser-session=LXDE-pi" | sudo tee -a "$LIGHTDM_CONF"
else
    sudo sed -i 's/^user-session=.*/user-session=LXDE-pi/' "$LIGHTDM_CONF"
fi

# Check for touchscreen device name
TOUCH_DEVICE=$(xinput list | grep -i "FT5406" | awk -F'[\t|id=]' '{print $1}' | xargs)

if [ -z "$TOUCH_DEVICE" ]; then
    echo "⚠️ Could not find FT5406 touchscreen device. Make sure you're in X11 and xinput is available."
    exit 1
fi

echo "✅ Found touchscreen device: \"$TOUCH_DEVICE\""

# Create rotate_touch.sh
echo "📄 Creating ~/rotate_touch.sh..."
cat <<EOF > ~/rotate_touch.sh
#!/bin/bash
sleep 5
xinput set-prop "$TOUCH_DEVICE" "Coordinate Transformation Matrix" -1 0 1 0 -1 1 0 0 1
EOF

chmod +x ~/rotate_touch.sh

# Create autostart entry
mkdir -p ~/.config/autostart
echo "🧩 Adding autostart entry..."
cat <<EOF > ~/.config/autostart/rotate-touch.desktop
[Desktop Entry]
Type=Application
Name=Rotate Touchscreen
Exec=/home/pi/rotate_touch.sh
X-GNOME-Autostart-enabled=true
EOF

echo "✅ Setup complete! Rebooting to apply changes..."
sleep 2
sudo reboot