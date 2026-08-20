# empire_game.py
# ملف لعبة حرب الإمبراطوريات الأسطورية - تصميم متكامل ومرئي بالكامل باللغة العربية

import sqlite3
import os
import io
import random
from PIL import Image, ImageDraw, ImageFont
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import ContextTypes

# إعداد قاعدة البيانات الخاصة باللعبة
DB_PATH = "empire_game.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # جدول الإمبراطوريات / اللاعبين مع نظام الدروع، الجنود، والمدرعات الحربية والتحالف
    cursor.execute('''CREATE TABLE IF NOT EXISTS empires (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        empire_name TEXT,
                        alliance_id INTEGER,
                        gold INTEGER DEFAULT 1500,
                        soldiers INTEGER DEFAULT 150,
                        armored_vehicles INTEGER DEFAULT 5,
                        shields INTEGER DEFAULT 5,
                        territories_count INTEGER DEFAULT 1,
                        color_code TEXT
                    )''')
                    
    # جدول التحالفات والأباطرة
    cursor.execute('''CREATE TABLE IF NOT EXISTS alliances (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        leader_id INTEGER,
                        gold_bank INTEGER DEFAULT 0
                    )''')
                    
    # جدول المقاطعات الخريطة (شبكة 4x4 مع مستويات وأنواع إنتاج)
    cursor.execute('''CREATE TABLE IF NOT EXISTS territories (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        owner_id INTEGER,
                        level INTEGER DEFAULT 1,
                        facility_type TEXT DEFAULT 'مزارع',
                        FOREIGN KEY(owner_id) REFERENCES empires(user_id)
                    )''')
                    
    conn.commit()
    conn.close()
    
    _seed_territories()

def _seed_territories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM territories")
    if cursor.fetchone()[0] == 0:
        names = ["بابل", "روما", "أثينا", "الإسكندرية", "قرطبة", "دمشق", "القسطنطينية", "قرطاج",
                 "طروادة", "سبارتا", "بغداد", "نينوى", "سوسة", "تدمر", "البتراء", "أوغاريت"]
        for i, name in enumerate(names):
            cursor.execute("INSERT INTO territories (id, name, owner_id) VALUES (?, ?, NULL)", (i+1, name))
        conn.commit()
    conn.close()

init_db()

# ==========================================
# محرك رسم الخريطة (نظيف بدون أسماء الأباطرة)
# ==========================================
def generate_3d_map_image():
    width, height = 1200, 950
    image = Image.new("RGB", (width, height), color=(11, 19, 43))
    draw = ImageDraw.Draw(image)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT T.id, T.name, T.owner_id, E.color_code 
        FROM territories T 
        LEFT JOIN empires E ON T.owner_id = E.user_id
    """)
    territories = cursor.fetchall()
    conn.close()

    try:
        font_title = ImageFont.truetype("arial.ttf", 26)
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        font_title = font = ImageFont.load_default()

    draw.text((350, 30), "👑 خريطة إمبراطورية مونوبولي الاستراتيجية 👑", fill=(212, 175, 55), font=font_title)

    start_x, start_y = 310, 130
    tile_w, tile_h = 240, 120

    idx = 0
    for row in range(4):
        for col in range(4):
            x = start_x + (col * 130) - (row * 130)
            y = start_y + (row * 75) + (col * 75)
            
            t_data = territories[idx] if idx < len(territories) else None
            
            box_color = (25, 38, 70)
            border_color = (212, 175, 55)
            
            if t_data and t_data[2] is not None:
                if t_data[3]:
                    try:
                        hex_c = t_data[3].lstrip('#')
                        box_color = tuple(int(hex_c[i:i+2], 16) for i in (0, 2, 4))
                    except:
                        box_color = (50, 70, 110)

            points = [
                (x, y + tile_h // 2),
                (x + tile_w // 2, y),
                (x + tile_w, y + tile_h // 2),
                (x + tile_w // 2, y + tile_h)
            ]
            
            draw.polygon(points, fill=box_color, outline=border_color)
            t_name = t_data[1] if t_data else f"منطقة {idx+1}"
            
            # عرض اسم الحصن/المقاطعة فقط بدون أسماء الأباطرة
            draw.text((x + 75, y + 45), f"🏰 {t_name}", fill=(255, 255, 255), font=font)
            
            idx += 1

    bio = io.BytesIO()
    bio.name = 'empire_map.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    return bio

# ==========================================
# محرك رسم صور المعارك البصرية اللحظية
# ==========================================
def generate_battle_image(attacker_name, target_name, result_won):
    width, height = 900, 500
    bg_color = (40, 10, 10) if not result_won else (10, 40, 20)
    image = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(image)

    try:
        font_large = ImageFont.truetype("arial.ttf", 32)
        font_medium = ImageFont.truetype("arial.ttf", 22)
    except:
        font_large = font_medium = ImageFont.load_default()

    draw.text((260, 40), "⚔️ ساحة المعركة الحربية الكبرى ⚔️", fill=(212, 175, 55), font=font_large)
    
    draw.rectangle([80, 120, 380, 380], fill=(25, 35, 60), outline=(212, 175, 55), width=3)
    draw.rectangle([520, 120, 820, 380], fill=(60, 20, 20), outline=(200, 50, 50), width=3)

    draw.text((120, 160), f"🛡️ المهاجم:", fill=(255, 255, 255), font=font_medium)
    draw.text((120, 210), f"{attacker_name[:15]}", fill=(212, 175, 55), font=font_large)

    draw.text((560, 160), f"🏰 المقاطعة المستهدفة:", fill=(255, 255, 255), font=font_medium)
    draw.text((560, 210), f"{target_name}", fill=(255, 100, 100), font=font_large)

    status_text = "🎉 انتصار ساحق واختراق للحصون!" if result_won else "⚠️ انكسار الهجوم وتصدي العدو!"
    status_color = (100, 255, 100) if result_won else (255, 100, 100)
    
    draw.text((250, 420), status_text, fill=status_color, font=font_medium)

    bio = io.BytesIO()
    bio.name = 'battle_result.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    return bio

# ==========================================
# واجهة الأوامر والأزرار
# ==========================================
def get_main_game_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🗺️ عرض الخريطة", callback_data="عرض الخريطة"),
            InlineKeyboardButton("🛡️ دروع الدفاع", callback_data="دروع الدفاع")
        ],
        [
            InlineKeyboardButton("⚔️ التجنيد", callback_data="التجنيد"),
            InlineKeyboardButton("🏛️ المقاطعات", callback_data="المقاطعات")
        ],
        [
            InlineKeyboardButton("💰 الخزينة", callback_data="الخزينة"),
            InlineKeyboardButton("🎯 قائمة الهجوم", callback_data="قائمة الهجوم")
        ],
        [
            InlineKeyboardButton("🤝 مركز التحالفات", callback_data="التحالفات")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_empire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.first_name

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM empires WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()

    if not existing:
        royal_colors = ["#1B365D", "#4A154B", "#2C5E1A", "#6E2C00", "#4A235A", "#154360"]
        chosen_color = random.choice(royal_colors)
        
        cursor.execute("INSERT INTO empires (user_id, username, empire_name, color_code) VALUES (?, ?, ?, ?)",
                       (user_id, username, f"إمبراطورية {username}", chosen_color))
        conn.commit()
        
        cursor.execute("SELECT id FROM territories WHERE owner_id IS NULL LIMIT 1")
        free_t = cursor.fetchone()
        if free_t:
            cursor.execute("UPDATE territories SET owner_id = ?, facility_type = 'مزارع' WHERE id = ?", (user_id, free_t[0]))
            conn.commit()
            
        conn.close()
        await update.message.reply_text(
            f"👑 **تهانينا يا قائد {username}!**\n"
            f"تم تأسيس إمبراطوريتك العظمى بنجاح وتم منحك مقاطعة البداية مع رصيد وافر لتبدأ رحلة المجد.\n\n"
            f"استخدم اللوحة أدناه لتدير إمبراطوريتك:",
            reply_markup=get_main_game_keyboard(),
            parse_mode="Markdown"
        )
    else:
        conn.close()
        await update.message.reply_text(
            f"🏰 **أهلاً بك مجدداً يا جلالة الإمبراطور {username}!**\n"
            f"إمبراطوريتك منتظرة أوامرك العسكرية:",
            reply_markup=get_main_game_keyboard(),
            parse_mode="Markdown"
        )

async def handle_game_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "عرض الخريطة":
        map_file = generate_3d_map_image()
        try:
            if query.message.photo:
                await query.message.edit_media(
                    media=InputMediaPhoto(media=map_file, caption="🗺️ **خريطة العالم الاستراتيجية**\nالمناطق الملونة تعود للأباطرة المسيطرين!", parse_mode="Markdown"),
                    reply_markup=get_main_game_keyboard()
                )
            else:
                await query.message.reply_photo(
                    photo=map_file,
                    caption="🗺️ **خريطة العالم الاستراتيجية**\nالمناطق الملونة تعود للأباطرة المسيطرين!",
                    reply_markup=get_main_game_keyboard(),
                    parse_mode="Markdown"
                )
        except Exception:
            await query.message.reply_photo(
                photo=map_file,
                caption="🗺️ **خريطة العالم الاستراتيجية**\nالمناطق الملونة تعود للأباطرة المسيطرين!",
                reply_markup=get_main_game_keyboard(),
                parse_mode="Markdown"
            )
        
    elif data == "دروع الدفاع":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT shields, gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()
        shields, gold = res if res else (5, 0)
        
        await safe_edit_or_reply(query, 
            f"🛡️ **نظام دروع الحماية الملكية**\n\n"
            f"دروعك الحالية: **{shields} من 5 دروع** (الحد الأقصى).\n"
            f"• كل هجوم يتعرض له دفاعك يستهلك درعاً واحداً.\n"
            f"• تكلفة شحن درع جديد: **200 قطعة ذهب**.\n\n"
            f"رصيدك الحالي في الخزينة: 💰 {gold} ذهبة",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("شراء درع جديد", callback_data="شراء درع")],
                [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
            ])
        )
        
    elif data == "شراء درع":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT shields, gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        
        if res:
            shields, gold = res
            if shields >= 5:
                await query.answer("دروعك في الحد الأقصى (5 دروع)! لا تحتاج للمزيد حالياً.", show_alert=True)
            elif gold < 200:
                await query.answer("عفواً، رصيدك من الذهب لا يكفي لشراء درع (تحتاج 200 ذهب).", show_alert=True)
            else:
                cursor.execute("UPDATE empires SET shields = shields + 1, gold = gold - 200 WHERE user_id = ?", (user_id,))
                conn.commit()
                await query.answer("تم شراء وشحن درع دفاعي بنجاح!", show_alert=True)
        conn.close()
        
        await handle_game_callbacks_refresh_shields(query, user_id)

    elif data == "التجنيد":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT soldiers, armored_vehicles, gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()
        soldiers, armored, gold = res if res else (150, 5, 0)
        
        await safe_edit_or_reply(query,
            f"⚔️ **ثكنة تجنيد الجيش والمدرعات الحربية**\n\n"
            f"• جنودك الحاليون: **{soldiers} جندي**\n"
            f"• مدرعاتك الحربية: **{armored} مدرعة**\n\n"
            f"خيارات التجنيد المتاحة:\n"
            f"1. تجنيد 50 جندي (التكلفة: 100 ذهب)\n"
            f"2. صنع مدرعة حربية ثقيلة (التكلفة: 200 ذهب)",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("تجنيد جنود", callback_data="تجنيد جنود")],
                [InlineKeyboardButton("صنع مدرعة", callback_data="صنع مدرعة")],
                [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
            ])
        )

    elif data == "تجنيد جنود":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        if res and res[0] >= 100:
            cursor.execute("UPDATE empires SET soldiers = soldiers + 50, gold = gold - 100 WHERE user_id = ?", (user_id,))
            conn.commit()
            await query.answer("تم تجنيد 50 جندي بنجاح وانضموا لصفوف جيشك!", show_alert=True)
        else:
            await query.answer("رصيدك من الذهب لا يكفي لتجنيد الجنود (تحتاج 100 ذهب).", show_alert=True)
        conn.close()
        await handle_game_callbacks_refresh_recruitment(query, user_id)

    elif data == "صنع مدرعة":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT gold FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        if res and res[0] >= 200:
            cursor.execute("UPDATE empires SET armored_vehicles = armored_vehicles + 1, gold = gold - 200 WHERE user_id = ?", (user_id,))
            conn.commit()
            await query.answer("تم تصنيع مدرعة حربية ثقيلة بنجاح!", show_alert=True)
        else:
            await query.answer("رصيدك من الذهب لا يكفي لصنع مدرعة (تحتاج 200 ذهب).", show_alert=True)
        conn.close()
        await handle_game_callbacks_refresh_recruitment(query, user_id)

    elif data == "المقاطعات":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, level, facility_type FROM territories WHERE owner_id = ?", (user_id,))
        territories = cursor.fetchall()
        conn.close()

        text = "🏛️ **إدارة مقاطعاتك ومستويات الإنتاج**\n\n• من المستوى 1 إلى 5: (تجميع سريع وسهل للذهب)\n• من المستوى 6 فما فوق: (صعوبة متوسطة وتتطلب استراتيجية)\n\nمناطقك الحالية:\n"
        keyboard_buttons = []
        for t in territories:
            t_id, t_name, t_lvl, t_fac = t
            text += f"• **{t_name}** | المستوى: {t_lvl} | المنشأة: {t_fac}\n"
            keyboard_buttons.append([InlineKeyboardButton(f"ترقية {t_name}", callback_data=f"ترقية {t_id}")])

        keyboard_buttons.append([InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")])
        await safe_edit_or_reply(query, text, InlineKeyboardMarkup(keyboard_buttons))

    elif data.startswith("ترقية "):
        t_id = int(data.split(" ")[1])
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT level, facility_type FROM territories WHERE id = ? AND owner_id = ?", (t_id, user_id))
        t_data = cursor.fetchone()
        
        if t_data:
            current_lvl, current_fac = t_data
            cursor.execute("SELECT gold FROM empires WHERE user_id = ?", (user_id,))
            gold_res = cursor.fetchone()
            gold = gold_res[0] if gold_res else 0
            
            upgrade_cost = (current_lvl * 150) if current_lvl <= 5 else (current_lvl * 500)
            
            if gold < upgrade_cost:
                await query.answer(f"الذهب غير كافٍ للترقية! تحتاج إلى {upgrade_cost} قطعة ذهبية.", show_alert=True)
            else:
                new_fac = "منجم ذهب أسطوري" if current_fac == "مزارع" else "مزارع"
                cursor.execute("UPDATE territories SET level = level + 1, facility_type = ? WHERE id = ?", (new_fac, t_id))
                cursor.execute("UPDATE empires SET gold = gold - ? WHERE user_id = ?", (upgrade_cost, user_id))
                conn.commit()
                await query.answer(f"تم ترقية المقاطعة بنجاح إلى المستوى {current_lvl + 1}!", show_alert=True)
        conn.close()
        await safe_edit_or_reply(query, "🏰 **تمت ترقية المقاطعة بنجاح وزادت قدرتها الإنتاجية!**", get_main_game_keyboard())

    elif data == "الخزينة":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT gold, soldiers, armored_vehicles, territories_count FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        conn.close()
        gold, soldiers, armored, territories_count = res if res else (1500, 150, 5, 1)
        
        await safe_edit_or_reply(query,
            f"💰 **الخزينة الملكية والموارد العامة**\n\n"
            f"• رصيد الذهب: **{gold} قطعة ذهبية**\n"
            f"• جنود الجيش: **{soldiers} جندي**\n"
            f"• المدرعات الحربية: **{armored} مدرعة**\n"
            f"• المقاطعات المسيطر عليها: **{territories_count} مقاطعة**",
            InlineKeyboardMarkup([
                [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
            ])
        )

    # ==========================================
    # مركز التحالفات (إنشاء فوري بدون قوائم جانبية)
    # ==========================================
    elif data == "التحالفات":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT alliance_id FROM empires WHERE user_id = ?", (user_id,))
        res = cursor.fetchone()
        a_id = res[0] if res else None
        
        if a_id:
            cursor.execute("SELECT name, gold_bank FROM alliances WHERE id = ?", (a_id,))
            a_data = cursor.fetchone()
            
            cursor.execute("SELECT empire_name FROM empires WHERE alliance_id = ?", (a_id,))
            members = cursor.fetchall()
            members_list = ", ".join([m[0] for m in members])
            
            conn.close()
            await safe_edit_or_reply(query,
                f"🤝 **مركز تحالف الأباطرة: {a_data[0]}**\n\n"
                f"💰 رصيد بنك التحالف: **{a_data[1]} قطعة ذهبية**\n"
                f"👥 أعضاء التحالف: {members_list}",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("مغادرة التحالف", callback_data="مغادرة_تحالف")],
                    [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
                ])
            )
        else:
            conn.close()
            await safe_edit_or_reply(query,
                f"🤝 **مركز التحالفات الاستراتيجية**\n\n"
                f"أنت لست منضماً لأي تحالف حالياً.\n"
                f"• يمكنك إنشاء تحالف عظيم خاص بك يكلف **1000 قطعة ذهبية** بضغطة زر.",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("إنشاء تحالف جديد", callback_data="إنشاء_تحالف")],
                    [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
                ])
            )

    elif data == "إنشاء_تحالف":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT alliance_id, gold, empire_name FROM empires WHERE user_id = ?", (user_id,))
        e_data = cursor.fetchone()
        
        if not e_data:
            conn.close()
            return
            
        a_id, gold, empire_name = e_data
        if a_id:
            conn.close()
            await query.answer("أنت منضم بالفعل لتحالف مسبقاً!", show_alert=True)
            return
            
        if gold < 1000:
            conn.close()
            await query.answer("رصيدك من الذهب لا يكفي لإنشاء تحالف (تحتاج إلى 1000 ذهب).", show_alert=True)
            return
            
        cursor.execute("INSERT INTO alliances (name, leader_id, gold_bank) VALUES (?, ?, 0)", (f"تحالف {empire_name}", user_id))
        new_a_id = cursor.lastrowid
        cursor.execute("UPDATE empires SET alliance_id = ?, gold = gold - 1000 WHERE user_id = ?", (new_a_id, user_id))
        conn.commit()
        conn.close()
        
        await query.answer("تم تأسيس تحالفك الأسطوري بنجاح!", show_alert=True)
        await handle_game_callbacks(update, context)

    elif data == "مغادرة_تحالف":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("UPDATE empires SET alliance_id = NULL WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        await query.answer("لقد غادرت التحالف بنجاح.", show_alert=True)
        await handle_game_callbacks(update, context)

    elif data == "قائمة الهجوم":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT T.id, T.name, T.owner_id, E.username FROM territories T LEFT JOIN empires E ON T.owner_id = E.user_id WHERE T.owner_id IS NULL OR T.owner_id != ?", (user_id,))
        targets = cursor.fetchall()
        conn.close()

        if not targets:
            await query.answer("لا توجد مقاطعات متاحة للهجوم حالياً، سحقت الجميع!", show_alert=True)
            return

        text = "⚔️ **قائمة أهداف الغزو العسكري المتاحة:**\nاختر مقاطعة لشن الهجوم البصري عليها:\n"
        keyboard_buttons = []
        for target in targets[:8]:
            t_id, t_name, owner_id, owner_name = target
            owner_label = f"مملكة: {owner_name}" if owner_name else "منطقة محايدة"
            keyboard_buttons.append([InlineKeyboardButton(f"هجوم على {t_name} ({owner_label})", callback_data=f"هجوم {t_id}")])

        keyboard_buttons.append([InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")])
        await safe_edit_or_reply(query, text, InlineKeyboardMarkup(keyboard_buttons))

    elif data.startswith("هجوم "):
        target_t_id = int(data.split(" ")[1])
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT soldiers, armored_vehicles, empire_name FROM empires WHERE user_id = ?", (user_id,))
        attacker_data = cursor.fetchone()
        
        cursor.execute("SELECT name, owner_id FROM territories WHERE id = ?", (target_t_id,))
        target_t_data = cursor.fetchone()
        
        if not attacker_data or not target_t_data:
            conn.close()
            await query.answer("حدث خطأ في بيانات الهجوم!", show_alert=True)
            return

        att_soldiers, att_armored, att_empire_name = attacker_data
        t_name, owner_id = target_t_data
        attacker_power = (att_soldiers * 1) + (att_armored * 50)

        # حساب القوة الدفاعية
        if owner_id is None:
            defender_power = 80
        else:
            cursor.execute("SELECT soldiers, armored_vehicles, shields FROM empires WHERE user_id = ?", (owner_id,))
            defender_empire = cursor.fetchone()
            if defender_empire:
                def_soldiers, def_armored, def_shields = defender_empire
                if def_shields > 0:
                    cursor.execute("UPDATE empires SET shields = shields - 1 WHERE user_id = ?", (owner_id,))
                    conn.commit()
                    conn.close()
                    await safe_edit_or_reply(query,
                        f"🛡️ **فشل الهجوم العسكري!**\n\n"
                        f"المقاطعة **{t_name}** محمية بدرع دفاعي ملكي!\nتم تدمير درع واحد للعدو دون تغيير السيطرة.",
                        get_main_game_keyboard()
                    )
                    return
                defender_power = (def_soldiers * 1) + (def_armored * 50) + 150
            else:
                defender_power = 100

        result_won = attacker_power >= defender_power

        if result_won:
            loot = random.randint(300, 700)
            cursor.execute("UPDATE territories SET owner_id = ?, level = 1, facility_type = 'مزارع' WHERE id = ?", (user_id, target_t_id))
            cursor.execute("UPDATE empires SET gold = gold + ?, territories_count = territories_count + 1 WHERE user_id = ?", (loot, user_id))
            
            if owner_id:
                cursor.execute("UPDATE empires SET territories_count = MAX(0, territories_count - 1) WHERE user_id = ?", (owner_id,))
            
            conn.commit()
        else:
            lost_soldiers = min(att_soldiers, random.randint(20, 50))
            cursor.execute("UPDATE empires SET soldiers = soldiers - ? WHERE user_id = ?", (lost_soldiers, user_id))
            conn.commit()

        # توليد صورة المعركة البصرية الفاخرة
        battle_img = generate_battle_image(att_empire_name, t_name, result_won)
        conn.close()

        try:
            await query.message.delete()
            await query.message.reply_photo(
                photo=battle_img,
                caption=f"⚔️ **نتيجة معركة الغزو المباشر**\nالمقاطعة: {t_name}",
                reply_markup=get_main_game_keyboard(),
                parse_mode="Markdown"
            )
        except Exception:
            pass

    elif data == "الرئيسية":
        await safe_edit_or_reply(query, "🏰 **لوحة تحكم الإمبراطورية الرئيسية:**", get_main_game_keyboard())

async def safe_edit_or_reply(query, text, reply_markup):
    try:
        if query.message.photo:
            await query.message.delete()
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception:
        try:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass

async def handle_game_callbacks_refresh_shields(query, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT shields, gold FROM empires WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    shields, gold = res if res else (5, 0)
    
    await safe_edit_or_reply(query,
        f"🛡️ **نظام دروع الحماية الملكية**\n\n"
        f"دروعك الحالية: **{shields} من 5 دروع**.\n"
        f"تكلفة شحن درع جديد: **200 قطعة ذهب**.\n\n"
        f"رصيدك الحالي: 💰 {gold} ذهبة",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("شراء درع جديد", callback_data="شراء درع")],
            [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
        ])
    )

async def handle_game_callbacks_refresh_recruitment(query, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT soldiers, armored_vehicles, gold FROM empires WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    soldiers, armored, gold = res if res else (150, 5, 0)
    
    await safe_edit_or_reply(query,
        f"⚔️ **ثكنة تجنيد الجيش والمدرعات الحربية**\n\n"
        f"• جنودك الحاليون: **{soldiers} جندي**\n"
        f"• مدرعاتك الحربية: **{armored} مدرعة**\n"
        f"• رصيد الذهب: 💰 {gold}",
        InlineKeyboardMarkup([
            [InlineKeyboardButton("تجنيد جنود", callback_data="تجنيد جنود")],
            [InlineKeyboardButton("صنع مدرعة", callback_data="صنع مدرعة")],
            [InlineKeyboardButton("الرئيسية", callback_data="الرئيسية")]
        ])
    )
