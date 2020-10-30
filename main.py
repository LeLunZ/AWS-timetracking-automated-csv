import time

from dataclasses import dataclass
from pynput.keyboard import Controller, Key
import csv
from datetime import datetime, timedelta


@dataclass
class ExportTime:
    in_time: datetime
    out_time: datetime
    remark: str


@dataclass
class Logs:
    date: str
    remark: str


csv_file = 'CHANGE IT'
ap_ = 'CHANGE IT'

if __name__ == '__main__':
    all_logs: [Logs] = []
    # for p in Path('./logs').iterdir():
    #    if p.is_file():
    #        with open(p) as file:
    #            lines = file.readlines()
    #           logs = list(
    #                map(lambda l: Logs(datetime.strptime(l.split(',')[0], '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y'),
    #                                   ', '.join(l.split(',')[1:]).strip()), lines))
    #            all_logs.extend(logs)
    exports = []
    with open(csv_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        next(reader, None)
        for in_action in reader:
            in_time = datetime.strptime(in_action[3], '%m-%d-%Y %H:%M:%S')
            remark_in = in_action[6]
            out_action = next(reader)
            out_time = datetime.strptime(out_action[3], '%m-%d-%Y %H:%M:%S')
            remark_out = out_action[6]
            if remark_out != '':
                remark = ', '.join([remark_in.strip(', \n\r"'), remark_out.strip(', \n\r"')])
            else:
                remark = remark_in.strip(', \n\r"')
            if (out_time - in_time).seconds >= (6 * 60 * 60):
                hour_before = out_time.hour
                out_time = out_time.replace(hour=in_time.hour + 4)
                exports.append(ExportTime(in_time, out_time, remark))
                new_in_time = out_time + timedelta(minutes=30)
                new_out_time = out_time.replace(hour=hour_before) + timedelta(minutes=30)
                exports.append(ExportTime(new_in_time, new_out_time, remark))
            else:
                exports.append(ExportTime(in_time, out_time, remark))

    from AppKit import NSWorkspace

    keyboard = Controller()
    activeAppName = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
    while 'Microsoft Excel' not in activeAppName:
        keyboard.press(Key.cmd)
        keyboard.press(Key.tab)
        keyboard.release(Key.cmd)
        keyboard.release(Key.tab)
        time.sleep(.5)
        activeAppName = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
    from AppKit import NSPasteboard, NSStringPboardType

    time.sleep(2)
    moveUp = False
    moveDown = False
    while True:
        keyboard.press(Key.cmd)
        keyboard.press('c')
        time.sleep(.1)
        keyboard.release(Key.cmd)
        keyboard.release('c')
        pb = NSPasteboard.generalPasteboard()
        pbstring = pb.stringForType_(NSStringPboardType)
        if pbstring == '':
            moveUp = True
        if pbstring != '':
            moveDown = True
        if moveUp and moveDown:
            break
        if moveUp:
            keyboard.press(Key.up)
        if moveDown:
            keyboard.press(Key.down)
    if pbstring != '':
        keyboard.press(Key.down)

    moveLeft = False
    moveRight = False
    while True:
        keyboard.press(Key.cmd)
        keyboard.press('c')
        time.sleep(.1)
        keyboard.release(Key.cmd)
        keyboard.release('c')
        pb = NSPasteboard.generalPasteboard()
        pbstring = pb.stringForType_(NSStringPboardType)
        if pbstring == '':
            moveLeft = True
        if pbstring != '':
            moveRight = True
        if moveLeft and moveRight:
            break
        if moveLeft:
            keyboard.press(Key.left)
        if moveRight:
            keyboard.press(Key.right)
    if pbstring != '':
        keyboard.press(Key.right)

    for export in exports:
        activeAppName = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
        while activeAppName != 'Microsoft Excel':
            time.sleep(2)
            activeAppName = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
        protocol_date = export.in_time.strftime("%d.%m.%Y")
        keyboard.type(protocol_date)
        keyboard.press(Key.tab)
        keyboard.type(export.in_time.strftime("%H"))
        keyboard.press(Key.tab)
        keyboard.type(export.in_time.strftime("%M"))
        keyboard.press(Key.tab)
        keyboard.type(export.out_time.strftime("%H"))
        keyboard.press(Key.tab)
        keyboard.type(export.out_time.strftime("%M"))
        keyboard.press(Key.tab)
        keyboard.type(ap_)
        keyboard.press(Key.tab)
        # git_remarks = list(map(lambda l: l.remark, filter(lambda l: l.date == protocol_date, all_logs)))
        # git_remarks.insert(0, export.remark)
        # export.remark = ', '.join(git_remarks)
        export.remark = export.remark.strip(', \n\r"')
        keyboard.type(export.remark)
        keyboard.press(Key.tab)

    exit(0)
