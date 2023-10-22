# High Level Analyzer
# For more information and documentation, please go to https://support.saleae.com/extensions/high-level-analyzer-extensions

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting

from enum import Enum

State = Enum('State', ['HEADER', 'CHANNELS', 'EXTRAS', 'FOOTER'])

SBUS_HEADER = 0x0F
SBUS_FOOTER = 0x00

NUM_CHANNELS = 16
BITS_PER_CHANNEL = 11
CHANNELS_BYTES = int((NUM_CHANNELS * BITS_PER_CHANNEL) / 8)

# High level analyzers must subclass the HighLevelAnalyzer class.
class Hla(HighLevelAnalyzer):
    # An optional list of types this analyzer produces, providing a way to customize the way frames are displayed in Logic 2.
    result_types = {
        'header': {
            'format': 'HEADER'
        },
        'footer': {
            'format': 'FOOTER'
        },
        'channel': {
            'format': '{{data.value}}'
        }
    }

    def __init__(self):
        '''
        Initialize HLA.

        Settings can be accessed using the same name used above.
        '''

        # print("Settings:", self.my_string_setting, self.my_number_setting, self.my_choices_setting)

        self.state = State.HEADER

        self.header_start = None
        self.header_end = None

        self.channel_byte_count = 0
        self.channel_bytes = [None] * CHANNELS_BYTES

        self.footer_start = None
        self.footer_end = None

    def decode(self, frame: AnalyzerFrame):
        output_frames = []

        # Get the byte for this frame
        b = [int(b) for b in frame.data['data']][0]

        # Check for the header at the start of the packet
        if self.state == State.HEADER:
            if b == SBUS_HEADER:
                # Capture the start and end time of this frame
                self.header_start = frame.start_time
                self.header_end = frame.end_time

                # Transition to waiting on channel data
                self.state = State.CHANNELS
        elif self.state == State.CHANNELS:
            # Capture the latest channel data
            self.channel_bytes[self.channel_byte_count] = b
            self.channel_byte_count += 1

            if self.channel_byte_count >= CHANNELS_BYTES:
                self.channel_byte_count = 0
                # Transition to EXTRAS state
                self.state = State.EXTRAS
        elif self.state == State.EXTRAS:
            # TODO: Capture extra IO

            # Transition to the FOOTER state
            self.state = State.FOOTER
        elif self.state == State.FOOTER:
            # Check for the packet end byte
            if b == SBUS_FOOTER:
                self.footer_start = frame.start_time
                self.footer_end = frame.end_time

                # Produce all frames
                output_frames.append(AnalyzerFrame('header', self.header_start, self.header_end, {}))
                output_frames.append(self.create_channel_frame(self.channel_bytes, self.header_end, self.footer_start))
                output_frames.append(AnalyzerFrame('footer', self.footer_start, self.footer_end, {}))

            # Always transition to the HEADER state
            self.state = State.HEADER

        return output_frames
    
    def create_channel_frame(self, channels_bytes, start_time, end_time):
        channel_data = [0] * 16
        
        channel_data[0]  = (channels_bytes[0] | ((channels_bytes[1] << 8) & 0x07FF))
        channel_data[1]  = ((channels_bytes[1] >> 3) | ((channels_bytes[2] << 5) & 0x07FF))
        channel_data[2]  = ((channels_bytes[2] >> 6) | (channels_bytes[3] << 2) | ((channels_bytes[4] << 10) & 0x07FF))
        channel_data[3]  = ((channels_bytes[4] >> 1) | ((channels_bytes[5] << 7) & 0x07FF))
        channel_data[4]  = ((channels_bytes[5] >> 4) | ((channels_bytes[6] << 4) & 0x07FF))
        channel_data[5]  = ((channels_bytes[6] >> 7) | (channels_bytes[7] << 1) | ((channels_bytes[8] << 9) & 0x07FF))
        channel_data[6]  = ((channels_bytes[8] >> 2) | ((channels_bytes[9] << 6) & 0x07FF))
        channel_data[7]  = ((channels_bytes[9] >> 5) | ((channels_bytes[10] << 3) & 0x07FF))
        channel_data[8]  = (channels_bytes[11] | ((channels_bytes[12] << 8) & 0x07FF))
        channel_data[9]  = ((channels_bytes[12] >> 3) | ((channels_bytes[13] << 5) & 0x07FF))
        channel_data[10] = ((channels_bytes[13] >> 6) | (channels_bytes[14] << 2) | ((channels_bytes[15] << 10) & 0x07FF))
        channel_data[11] = ((channels_bytes[15] >> 1) | ((channels_bytes[16] << 7) & 0x07FF))
        channel_data[12] = ((channels_bytes[16] >> 4) | ((channels_bytes[17] << 4) & 0x07FF))
        channel_data[13] = ((channels_bytes[17] >> 7) | (channels_bytes[18] << 1) | ((channels_bytes[19] << 9) & 0x07FF))
        channel_data[14] = ((channels_bytes[19] >> 2) | ((channels_bytes[20] << 6) & 0x07FF))
        channel_data[15] = ((channels_bytes[20] >> 5) | ((channels_bytes[21] << 3) & 0x07FF))

        data_string = ''
        for (i, data) in enumerate(channel_data):
            data_string += f'ch{i + 1}: {data}, '

        return AnalyzerFrame('channel', start_time, end_time, {'value': data_string})
