import json
import pickle
import random
import time

import argparse

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Dict

import csv
from datetime import datetime, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from xlsxwriter import Workbook

allg_feiertage = []

months = {
    'Jan': 1,
    'Feb': 2,
    'Mär': 3,
    'Apr': 4,
    'Mai': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Okt': 10,
    'Nov': 11,
    'Dez': 12
}


def load_allg_feiertage():
    years = set(
        [start_date_time.date().year + i for i in range(end_date_time.date().year - start_date_time.date().year + 1)])

    global allg_feiertage
    feier_f = Path('data/feiertage.pickle')
    if feier_f.is_file():
        with open(feier_f, 'rb') as f:
            allg_feiertage = pickle.load(f)
        distinct_years = set([f.year for f in allg_feiertage])
        if all(x in distinct_years for x in years):
            return

    driver = webdriver.Chrome('../aptc/chromedriver')
    for year in years:
        driver.get('https://www.timeanddate.de/feiertage/oesterreich/' + str(year))
        WebDriverWait(driver, 7).until(EC.presence_of_element_located((By.XPATH, '//*/tbody')))
        try:
            cookie_ok = driver.find_element(By.XPATH,
                                            "//*/button[contains(@class, 'fc-button') and contains(@class, 'fc-cta-consent') and contains(@class,'fc-primary-button')]")

            cookie_ok.click()
        except EC.NoSuchElementException:
            pass
        elements = driver.find_elements(By.XPATH, "//*/tbody/tr[@class='showrow']/th")

        for f in elements:
            f_split = f.text.split(' ')
            day = int(f_split[0].replace('.', ''))
            month = f_split[1]
            year = year
            allg_feiertage.append(datetime(year, months[month], day).date())
    with open(feier_f, 'wb') as f:
        pickle.dump(allg_feiertage, f)
    driver.quit()


@dataclass
class ExportTime:
    in_time: datetime
    out_time: datetime
    remark: str
    is_generated: bool = False
    ap: str = None


class ExportDay:
    def __init__(self, day):
        self.times = []
        self.day: datetime = day
        self.work_hours = 0  # in seconds
        self.valid: bool = True
        self.validation_str = []

    def add_times(self, e_time: ExportTime):
        self.times.append(e_time)

        self.work_hours += (e_time.out_time - e_time.in_time).total_seconds()

    def add_validation(self, text):
        self.valid = False
        self.validation_str.append(text)


@dataclass
class Logs:
    date: datetime
    remarks: str


def convert_git_time(git_time):
    try:
        return datetime.strptime(git_time.split(',')[0], '%Y-%m-%d %H:%M:%S %z')
    except:
        return datetime.strptime(git_time.split(',')[0], '%Y-%m-%d %H:%M:%S')


all_logs = {}


def prepare_logs():
    for p in Path(git_logs).iterdir():
        if p.is_file():
            with open(p) as file:
                lines = file.readlines()
                logs = list(
                    map(lambda l: Logs(convert_git_time(l),
                                       ', '.join(l.split(',')[1:]).strip()), lines))
                for l in logs:
                    key = l.date.date()
                    if key not in all_logs:
                        all_logs[key] = [l.remarks]
                    elif l.remarks not in all_logs[key]:
                        all_logs[key].append(l.remarks)
                    else:
                        date_r = l.date
                        while key not in all_logs and date_r.year == 2020:
                            date_r = date_r + timedelta(days=1)
                            key = date_r.strftime('%d.%m.%Y')
                        all_logs[key].append(l.remarks)

    export = {k.strftime("%d.%m.%Y"): all_logs[k] for k in all_logs}
    with open('log.json', 'w') as f:
        json.dump(export, f)


export_days = {}
user = None


def add_export_time(day: datetime, e_time: ExportTime):
    day = day.date()
    if day in export_days:
        export_days[day].add_times(e_time)
    else:
        export_days[day] = ExportDay(day)
        export_days[day].add_times(e_time)


def get_export_time(day):
    try:
        return export_days[day]
    except KeyError:
        return None


def remove_export_time(day):
    return export_days.pop(day, None)


@dataclass
class WorkTimes:
    begin: List = field(default_factory=lambda: [])
    end: List = field(default_factory=lambda: [])


def read_old_aws_sheet():
    csv_name = Path(str(args.aws).strip())
    min_ = datetime.max
    max_ = datetime.min
    with open(csv_name, 'r') as csv_f:
        csv_time_sheet = csv.reader(csv_f,delimiter=';', quotechar='"', skipinitialspace=True)
        # 01.09.20;11;:00;13;:15;2:15;2,25;AP 3;Working from Home: Rewriting the AuthService because it needs to be done., added new stop in location loading
        for line in csv_time_sheet:
            if len(line) == 0:
                break
            if line[0] == '':
                continue
            d = datetime.strptime(line[0], '%d.%m.%y')
            min_ = min(d, min_)
            max_ = max(d, max_)
            in_time = d.replace(hour=int(line[1]), minute=int(line[2][1:]))
            out_time = d.replace(hour=int(line[3]), minute=int(line[4][1:]))
            ap = line[7]
            remark = line[8]
            add_export_time(d, ExportTime(in_time, out_time, remark, ap=ap))

    return min_, max_


def read_time_sheet():
    global user
    time_sheet_file = Path(input('Timesheet: ').strip())
    time_sheet_data = []
    with open(time_sheet_file, 'r') as time_sheet:
        time_sheet.readline()  # Unused
        time_sheet.readline()  # Unused
        user = time_sheet.readline().removeprefix('Generated by ').strip()  # Name
        time_sheet.readline()  # Unused
        time_sheet.readline()  # Empty
        time_sheet.readline()  # Empty
        csv_time_sheet = csv.reader(time_sheet, quotechar='"', skipinitialspace=True)
        header: List = [h.strip() for h in next(csv_time_sheet)]  # Header

        action = header.index('Action Type')
        timestamp = header.index('Timestamp')
        remark = header.index('Remark')

        # in action is first in csv. And in for we always skip one line.
        for in_action in csv_time_sheet:
            if len(in_action) == 0:
                break
            in_time = datetime.strptime(in_action[timestamp], '%m-%d-%Y %I:%M %p')
            remark_in = in_action[remark]
            out_action = next(csv_time_sheet)  # get next line
            if len(out_action) == 0:
                break
            out_time = datetime.strptime(out_action[timestamp], '%m-%d-%Y %I:%M %p')
            remark_out = out_action[remark]

            if remark_out != '' != remark_in and remark_out != remark_in:
                remark_str = ', '.join([remark_in.strip(', \n\r"'), remark_out.strip(', \n\r"')])
            elif remark_out != '':
                remark_str = remark_out.strip(', \n\r"')
            elif remark_in != '':
                remark_str = remark_in.strip(', \n\r"')
            else:
                remark_str = ''
            if (out_time - in_time).seconds >= (6 * 60 * 60):
                hour_before = out_time.hour
                out_time = out_time.replace(hour=in_time.hour + 4)
                time_sheet_data.append(ExportTime(in_time, out_time, remark_str))
                add_export_time(in_time, time_sheet_data[-1])
                new_in_time = out_time + timedelta(minutes=30)
                new_out_time = out_time.replace(hour=hour_before) + timedelta(minutes=30)
                time_sheet_data.append(ExportTime(new_in_time, new_out_time, remark_str))
                add_export_time(in_time, time_sheet_data[-1])
            else:
                time_sheet_data.append(ExportTime(in_time, out_time, remark_str))
                add_export_time(in_time, time_sheet_data[-1])

    return time_sheet_data


def validate_export(use_git_logs):
    days = ['MO', 'DI', 'MI', 'DO', 'FR', 'SA', 'SO']

    week_end_date = (start_date_time + timedelta(days=6 - start_date_time.weekday())).date()
    week_start_date = start_date_time.date()

    all_exports = []
    if args.aws is not None:
        old_min, old_max = read_old_aws_sheet()
        for export_date in [old_min.date() + timedelta(days=x) for x in
                            range(1 + (old_max.date() - old_min.date()).days)]:
            export: ExportDay = get_export_time(export_date)
            if export is not None:
                all_exports.append(export)
    overdue = []
    for export_date in [week_start_date + timedelta(days=x) for x in
                        range(1 + (end_date_time.date() - week_start_date).days)]:
        export = get_export_time(export_date)
        if export is not None:
            if export_date in allg_feiertage or export_date.weekday() == 6:
                exp = remove_export_time(export_date)
                exp.add_validation(f'Moved from {export_date}, Sonntag or Feiertag!!!')
                overdue.append(exp)
    overdue.reverse()

    while week_end_date <= end_date_time.date() + timedelta(days=1):
        work_hours = 0
        added_work_hours = 0
        added_work = []
        for export_date in [week_start_date + timedelta(days=x) for x in
                            range(1 + (week_end_date - week_start_date).days)]:
            export: ExportDay = get_export_time(export_date)
            if export is not None:
                if export.work_hours > 10 * 60 * 60:
                    export.valid = False
                    export.add_validation(f'Too Many Work Hours {export.work_hours / 60 / 60}. Max: 10')
                work_hours += export.work_hours
                all_exports.append(export)
                if export_date.weekday() == 5:
                    export.add_validation('Samstag?!')
            else:
                if export_date not in allg_feiertage and export_date.weekday() != 5 and export_date.weekday() != 6:
                    found_elems = [o for o in overdue if abs((o.day - export_date).days) <= 7]
                    if len(found_elems) > 0:
                        take = found_elems[0]
                        overdue.remove(take)
                        if take.work_hours > 10 * 60 * 60:
                            take.valid = False
                            take.add_validation(f'Too Many Work Hours {take.work_hours / 60 / 60}')
                        take.day = export_date
                        all_exports.append(take)
                        work_hours += take.work_hours
                    elif generate_working_hours.strip() != 'n':
                        day = ExportDay(export_date)
                        if daily_hours == 7.75:
                            begin = datetime(year=export_date.year, month=export_date.month, day=export_date.day,
                                             hour=8,
                                             minute=30)
                            end = datetime(year=export_date.year, month=export_date.month, day=export_date.day, hour=12,
                                           minute=00)
                            day.add_times(ExportTime(begin, end, '', True))
                            begin = datetime(year=export_date.year, month=export_date.month, day=export_date.day,
                                             hour=12,
                                             minute=30)
                            end = datetime(year=export_date.year, month=export_date.month, day=export_date.day, hour=16,
                                           minute=45)
                            day.add_times(ExportTime(begin, end, '', True))
                        else:
                            if with_break:
                                before_break_hours = int(daily_hours / 2)
                                after_break_minutes = int((daily_hours - int(daily_hours)) * 60 + 30)
                                begin = datetime(year=export_date.year, month=export_date.month, day=export_date.day,
                                                 hour=12 - before_break_hours,
                                                 minute=0)
                                end = datetime(year=export_date.year, month=export_date.month, day=export_date.day,
                                               hour=12,
                                               minute=30)
                                day.add_times(ExportTime(begin, end, '', True))
                                begin = datetime(year=export_date.year, month=export_date.month, day=export_date.day,
                                                 hour=12,
                                                 minute=30)
                                end = datetime(year=export_date.year, month=export_date.month, day=export_date.day,
                                               hour=(12 + before_break_hours + 1) if after_break_minutes >= 60 else (
                                                       12 + before_break_hours),
                                               minute=(
                                                       after_break_minutes - 60) if after_break_minutes >= 60 else after_break_minutes)
                                day.add_times(ExportTime(begin, end, '', True))
                            else:
                                randy_min = random.randint(0, 3) * 15
                                begin = datetime(year=export_date.year, month=export_date.month, day=export_date.day,
                                                 hour=8,
                                                 minute=randy_min)
                                work_end_min = randy_min + int((daily_hours - int(daily_hours)) * 60)
                                work_end_hour = 8 + int(daily_hours)
                                if work_end_min >= 60:
                                    work_end_min = work_end_min - 60
                                    work_end_hour = work_end_hour + 1
                                end = datetime(year=export_date.year, month=export_date.month, day=export_date.day,
                                               hour=work_end_hour,
                                               minute=work_end_min)
                                day.add_times(ExportTime(begin, end, '', True))
                        added_work_hours += day.work_hours
                        added_work.append(day)
        if work_hours > weekly_hours * 60 * 60:
            all_exports[-1].add_validation(
                f'{work_hours / 60 / 60} hours worked in the week. {weekly_hours} should be done')
        if work_hours < weekly_hours * 60 * 60:
            while len(added_work) > 0 and (weekly_hours - work_hours / 60 / 60) > 1.5:
                to_add = added_work.pop(0)
                all_exports.append(to_add)
                work_hours += to_add.work_hours
            all_exports.sort(key=lambda x: x.day)
            all_exports[-1].add_validation(
                f'{work_hours / 60 / 60} hours worked in the week. {weekly_hours} should be done')
        week_start_date = week_end_date + timedelta(days=1)
        if week_end_date + timedelta(days=7) > end_date_time.date() and week_end_date != end_date_time.date():
            week_end_date = end_date_time.date()
        else:
            week_end_date = week_end_date + timedelta(days=7)

    if use_git_logs:
        for e in all_exports:
            if e.day in all_logs:
                empty_remark = [t for t in e.times if t.remark == '']
                all_e = [t for t in e.times]
                for l in all_logs[e.day]:
                    if len(empty_remark) > 0:
                        r = empty_remark.pop(0)
                        r.remark = l
                    else:
                        r = all_e.pop(0)
                        all_e.append(r)
                        r.remark += f', {l}'
                del all_logs[e.day]

        export_logs = {k.strftime("%d.%m.%Y"): all_logs[k] for k in all_logs}
        with open('unused-logs.json', 'w') as f:
            json.dump(export_logs, f)

    f_name = f'{str(user).replace(" ", "_")}_timesheet_{start_date_time.strftime("%m_%Y")}_to_{end_date_time.strftime("%m_%Y")}'
    export_len = 0
    with open(f'{f_name}.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(
            ['Weekday', 'Date', 'Check In Time', 'Check Out Time', 'Work Time', 'Work Package', 'Remark', 'Generated',
             'Validation'])

        for e_day in all_exports:
            for t in e_day.times[:-1]:
                export_len += 1
                csv_writer.writerow(
                    [days[e_day.day.weekday()], e_day.day.strftime('%d.%m.%Y'), t.in_time.strftime('%H:%M'),
                     t.out_time.strftime('%H:%M'), (t.out_time - t.in_time).total_seconds() / 60 / 60, ap_ if t.ap is None else t.ap, t.remark,
                     '*' if t.is_generated else '', ''])
            t: ExportTime = e_day.times[-1]
            export_len += 1
            csv_writer.writerow([days[e_day.day.weekday()], e_day.day.strftime('%d.%m.%Y'), t.in_time.strftime('%H:%M'),
                                 t.out_time.strftime('%H:%M'), (t.out_time - t.in_time).total_seconds() / 60 / 60, ap_ if t.ap is None else t.ap,
                                 t.remark, '*' if t.is_generated else ''] + (
                                    [''] if e_day.valid else e_day.validation_str))
        if len(overdue) != 0:
            csv_writer.writerow([])
            csv_writer.writerow([])
            csv_writer.writerow([])
            csv_writer.writerow(
                ['Worktimes from Sunday and public Holidays. Insert these elsewhere with another date.'])
            for e_day in overdue:
                for t in e_day.times:
                    csv_writer.writerow(
                        [days[e_day.day.weekday()], e_day.day.strftime('%d.%m.%Y'), t.in_time.strftime('%H:%M'),
                         t.out_time.strftime('%H:%M'), (t.out_time - t.in_time).total_seconds() / 60 / 60, ap_ if t.ap is None else t.ap,
                         t.remark,
                         '*' if t.is_generated else '', ''])
    print(f'file exported to {f_name}')
    workbook = Workbook(f_name + '.xlsx')
    worksheet = workbook.add_worksheet()

    hour_minutes = workbook.add_format({'num_format': 'h:mm'})
    date_format = workbook.add_format({'num_format': 'dd.mm.yyyy'})

    with open(f_name + '.csv', 'rt', encoding='utf8') as f:
        reader = csv.reader(f)
        for r, row in enumerate(reader):
            for c, col in enumerate(row):
                if r > 0 and c == 1:
                    worksheet.write(r, c, col, date_format)
                elif r > 0 and (c == 2 or c==3):
                    worksheet.write(r, c, col, hour_minutes)
                else:
                    worksheet.write(r, c, col, )

    for l in range(1, export_len + 1):
        worksheet.write_formula(f'E{l + 1}', '{=' + f'D{l + 1}-C{l + 1}' + '}', hour_minutes)
    workbook.close()
    return


def export_to_aws_csv():
    raise NotImplementedError('Dont use this method\nTODO implement conversion from all_logs to export strs')
    from pynput.keyboard import Controller, Key

    try:
        from AppKit import NSWorkspace
    except ImportError as e:
        print('Please install PyObjC. pip3 install PyObjC')
        exit(0)
    cn = 1
    keyboard = Controller()
    activeAppName = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
    while 'Microsoft Excel' not in activeAppName:
        keyboard.press(Key.cmd)
        for i in range(0, cn):
            keyboard.press(Key.tab)
            time.sleep(.1)
            keyboard.release(Key.tab)
        keyboard.release(Key.cmd)
        time.sleep(0.5)
        activeAppName = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
        cn = cn + 1
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

    export_strs = []  # TODO implement conversion from all_logs to export strs
    for entries in all_logs:
        activeAppName = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']
        while activeAppName != 'Microsoft Excel':
            time.sleep(2)
            activeAppName = NSWorkspace.sharedWorkspace().activeApplication()['NSApplicationName']

        for i in entries[:-1]:
            keyboard.type(str(i))
            keyboard.press(Key.tab)

        remark = ','.join(entries[-1])
        keyboard.type(remark)
        keyboard.press(Key.tab)


def export_to_csv():
    time_tracking_row = []
    with open('output', 'w') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(time_tracking_row)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AWS Tool', usage='main.py [-options] {Utility}')
    parser.add_argument('--aws',
                        help='Path to old aws-csv copy')
    parser.add_argument('--csv',
                        help='Path to old csv')
    args = parser.parse_args()
    start_date_time = datetime.strptime(input('Start Date (Format dd.mm.YYYY): '), '%d.%m.%Y')
    end_date_time = datetime.strptime(input('End Date (Format dd.mm.YYYY): '), '%d.%m.%Y')
    generate_working_hours = input('Do you want to generate working hours (please use if you didn\'t use attendancebot much). (y/n): ')
    part_time = input('Do you work part time. (y/n)')
    if part_time == 'y':
        weekly_hours = float(input('Weekly Hours (zb. 23.5): '))
        daily_hours = float(input('Daily Hours (zb. 6.5): '))
        if daily_hours < 6:
            with_break = float(input('Do you do a lunch break? (or work all hours without lunch) (y/n): '))
        else:
            with_break = True
    else:
        weekly_hours = 38.5
        daily_hours = 7.75
        with_break = True
    ap_ = input('Default Arbeitsparket (zb. AP 3): ')
    git_logs = input('Git Log Folder (Press Enter to skip): ').strip()
    export_to_aws = input('Export also to AWS Timesheet (y/n): ')
    load_allg_feiertage()
    if git_logs != '':
        git_logs = Path(git_logs)
        prepare_logs()
    read_time_sheet()
    validate_export(git_logs != '')
    if export_to_aws != 'n' and export_to_aws != '':
        export_to_aws_csv()
    exit(0)
