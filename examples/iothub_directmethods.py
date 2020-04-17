import time
import board
import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
from adafruit_ntp import NTP

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# ESP32 Setup
try:
    esp32_cs = DigitalInOut(board.ESP_CS)
    esp32_ready = DigitalInOut(board.ESP_BUSY)
    esp32_reset = DigitalInOut(board.ESP_RESET)
except AttributeError:
    esp32_cs = DigitalInOut(board.D13)
    esp32_ready = DigitalInOut(board.D11)
    esp32_reset = DigitalInOut(board.D12)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets)
wifi.connect()

ntp = NTP(esp)
# Wait for a valid time to be received
while not ntp.valid_time:
    time.sleep(5)
    ntp.set_time()

# You will need an Azure subscription to create an Azure IoT Hub resource
#
# If you don't have an Azure subscription:
#
# If you are a student, head to https://aka.ms/FreeStudentAzure and sign up, validating with your
#  student email address. This will give you $100 of Azure credit and free tiers of a load of
#  service, renewable each year you are a student
#
# If you are not a student, head to https://aka.ms/FreeAz and sign up to get $200 of credit for 30
#  days, as well as free tiers of a load of services
#
# Create an Azure IoT Hub and an IoT device in the Azure portal here: https://aka.ms/AzurePortalHome.
# Instructions to create an IoT Hub and device are here: https://aka.ms/CreateIoTHub
#
# The free tier of IoT Hub allows up to 8,000 messages a day, so try not to send messages too often
# if you are using the free tier
#
# Once you have a hub and a device, copy the device primary connection string.
# Add it to the secrets.py file in an entry called device_connection_string

from adafruit_azureiot import IoTHubDevice
from adafruit_azureiot.iot_mqtt import IoTResponse

# Create an IoT Hub device client and connect
device = IoTHubDevice(wifi, secrets["device_connection_string"])

# Subscribe to direct method calls
# To invoke a method on the device, select it in the Azure Portal, select Direct Method,
# fill in the method name and payload, then select Invoke Method
# Direct method handlers need to return a response to show if the method was handled
# successfully or not, returning an HTTP status code and message
def direct_method_invoked(method_name: str, payload) -> IoTResponse:
    print("Received direct method", method_name, "with data", str(payload))
    # return a status code and message to indicate if the direct method was handled correctly
    return IoTResponse(200, "OK")


device.on_direct_method_invoked = direct_method_invoked

device.connect()

while True:
    # Poll every second for messages from the cloud
    device.loop()

    time.sleep(1)
