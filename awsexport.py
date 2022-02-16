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