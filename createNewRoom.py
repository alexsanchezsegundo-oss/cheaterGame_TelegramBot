import main, random
def createRooms(roomsLength):
    if roomsLength > 10:
        print("not rooms enough. Have to wait :(")
        return None
    if roomsLength <= 10:
        print("Creating a room...")
        room_number = random.randrange(1000, 99990)
        print(str(room_number) + " is the room")
        return room_number
    





