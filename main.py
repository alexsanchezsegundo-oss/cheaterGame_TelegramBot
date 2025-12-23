import os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
import private, messages, createNewRoom

api_key = private.api_key
rooms = {} 


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        text=messages.welcomeMsg, 
        reply_markup=reply_markup
    )
async def createRoom(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get('created_room'):
        await update.effective_message.reply_text(messages.stillARoomAssigned)
        return

    tempRoom = createNewRoom.createRooms(len(rooms))
    if tempRoom is None:
        await update.effective_message.reply_text(messages.noRoomsAvailable)
        return 

    rooms[tempRoom] = {"players": [], "owner": update.effective_user.id}
    context.user_data['created_room'] = tempRoom

    keyboard = [[InlineKeyboardButton("🚀 Join Room", callback_data=f"join_{tempRoom}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.effective_message.reply_text(
        text=f"{messages.roomAssigned}\nID: `{tempRoom}`",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    if state == 'waiting_for_id':
        room_id_input = update.message.text
        
        if not room_id_input.isdigit():
            await update.message.reply_text("❌ Invalid ID. Please send numbers only.")
            return

        room_id = int(room_id_input)
        
        if room_id in rooms:
            user = update.effective_user.username
            nickname = f"@{user}" if user else update.effective_user.first_name
            
            if nickname not in rooms[room_id]["players"]:
                rooms[room_id]["players"].append(nickname)
                context.user_data['current_room'] = room_id
                context.user_data['state'] = None # Clear state
                
                players = ", ".join(rooms[room_id]["players"])
                await update.message.reply_text(
                    text=f"✅ Joined! Room: {room_id}\nPlayers: {players}",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🚪 Exit", callback_data=f"exit_{room_id}")]])
                )
            else:
                await update.message.reply_text("You are already in this room!")
        else:
            await update.message.reply_text("❌ Room not found. Try again or type /start.")
async def process_join(query, context, room_id):
    user = query.from_user.username
    nickname = f"@{user}" if user else query.from_user.first_name
    
    if room_id in rooms:
        if nickname not in rooms[room_id]["players"]:
            rooms[room_id]["players"].append(nickname)
            context.user_data['current_room'] = room_id
            
            keyboard = [[InlineKeyboardButton("🎮 Play", callback_data="game_play")]]
            await query.edit_message_text(
                text=f"✅ Joined Room {room_id}. Click below to enter the lobby.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )





async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    section = parts[0] 
    choice = parts[1]
    if section == "lang":
        context.user_data['lang'] = choice.upper()
        
        keyboard = [
            [InlineKeyboardButton("➕ Create Room", callback_data="menu_create")],
            [InlineKeyboardButton("🚪 Join Room", callback_data="menu_join")]
        ]
        await query.edit_message_text(
            text="Main Menu: What would you like to do?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    elif section == "menu":
        if choice == "create":
            await createRoom(update, context)
        elif choice == "join":
            context.user_data['state'] = 'waiting_for_id'
            await query.edit_message_text(text="Please send the Room ID to join.")

    elif section == "join":
        room_id = int(choice)
        user = query.from_user.username
        nickname = f"@{user}" if user else query.from_user.first_name
        
        if room_id in rooms:
            if nickname not in rooms[room_id]["players"]:
                rooms[room_id]["players"].append(nickname)
                context.user_data['current_room'] = room_id
                
                players_list = ", ".join(rooms[room_id]["players"])
                await query.edit_message_text(
                    text=f"✅ Joined! Room: {room_id}\nPlayers: {players_list}",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("⬅️ Back to Menu", callback_data="lang_en") 
                    ]])
                )
            else:
                await query.answer(text="Already in!", show_alert=True)
        else:
            await query.edit_message_text(text="❌ Room no longer exists.")

    elif section == "game":
        room_id = context.user_data.get('current_room')
        
        if choice == "play": 
            players = ", ".join(rooms[room_id]["players"])
            keyboard = [[InlineKeyboardButton("🔥 Begin Play", callback_data=f"game_start")]]

            # Only owner should see "Begin Play", others see "Waiting..."
            if update.effective_user.id != rooms[room_id]["owner"]:
                keyboard = [[InlineKeyboardButton("⌛ Waiting for host...", callback_data="none")]]
            
            await query.edit_message_text(
                text=f"Lobby - Room {room_id}\nPlayers: {players}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        elif choice == "start": # Starts the Match
            if update.effective_user.id == rooms[room_id]["owner"]:
                # Logic to assign roles goes here
                await query.edit_message_text(text="🎲 Game started! Check your private messages for roles.")
            else:
                await query.answer("Only the host can start the game!", show_alert=True)









if __name__ == '__main__':
    application = ApplicationBuilder().token(api_key).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(handle_button_click))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_input))

    application.run_polling()