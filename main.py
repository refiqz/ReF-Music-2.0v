import asyncio
import maniac  # استيراد ملف maniac.py

          # تشغيل البوت باستخدام asyncio
if __name__ == "__main__":
              print("Starting the bot...")
              loop = asyncio.new_event_loop()
              asyncio.set_event_loop(loop)
try:
                  # بدء تشغيل البوت
                  loop.create_task(maniac.client.start(maniac.TOKEN))
                  loop.run_forever()  # تشغيل حلقة الحدث بشكل دائم
except KeyboardInterrupt:
                  print("Shutting down the bot...")
                  loop.run_until_complete(maniac.client.logout())  # إيقاف البوت بأمان
                  loop.close()