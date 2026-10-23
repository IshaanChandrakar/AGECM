"""Disabled developer utility: this task never authorizes writes to sensing channels."""
import os
from adapter import Http

def validate_write(response, expected_channel):
 if not isinstance(response,dict) or not isinstance(response.get('entry_id'),int) or isinstance(response.get('entry_id'),bool) or response['entry_id']<=0:
  raise ValueError('ThingSpeak rejected write: no positive entry ID')
 if str(response.get('channel_id'))!=str(expected_channel):raise ValueError('Unexpected test channel')
 return response['entry_id']

def main():
 if os.getenv('ENABLE_THINGSPEAK_WRITE_TEST')!='true':raise SystemExit('Write testing is disabled. Separate explicit authorization for a dedicated test channel is required.')
 channel=os.getenv('THINGSPEAK_TEST_CHANNEL_ID');key=os.getenv('THINGSPEAK_TEST_WRITE_KEY')
 if not channel or not key or channel in [os.getenv('THINGSPEAK_NODE1_CHANNEL_ID'),os.getenv('THINGSPEAK_NODE2_CHANNEL_ID')]:raise SystemExit('A separate dedicated test channel and key are required')
 # All eight fields follow the actual contract; no sensing-channel writes are performed.
 payload=dict(api_key=key,field1=0,field2=0,field3=0,field4=0,field5=0,field6=0,field7=0,field8=0)
 result=Http(retries=0).request('POST','https://api.thingspeak.com/update.json',payload)
 print('Accepted dedicated test entry:',validate_write(result,channel))
if __name__=='__main__':main()
