---
description: الرفع والتحديث على Railway
---

استخدم هذا الـ Workflow لرفع التعديلات الحالية من جهازك المحلي إلى سيرفر Railway.

1. التأكد من حالة الملفات
// turbo
run_command(CommandLine="git status", Cwd="c:\\Users\\dell\\Desktop\\gold", SafeToAutoRun=true, WaitMsBeforeAsync=500)

2. إضافة جميع التعديلات
// turbo
run_command(CommandLine="git add .", Cwd="c:\\Users\\dell\\Desktop\\gold", SafeToAutoRun=true, WaitMsBeforeAsync=500)

3. تسجيل التعديلات (Commit)
// turbo
run_command(CommandLine="git commit -m \"Updates and fixes via Antigravity\"", Cwd="c:\\Users\\dell\\Desktop\\gold", SafeToAutoRun=true, WaitMsBeforeAsync=500)

4. الرفع إلى GitHub لتحديث الموقع
// turbo
run_command(CommandLine="git push origin main", Cwd="c:\\Users\\dell\\Desktop\\gold", SafeToAutoRun=true, WaitMsBeforeAsync=500)

5. إبلاغ المستخدم
notify_user(Message="تم رفع التعديلات بنجاح. يرجى الانتظار دقيقة واحدة لتحديث الموقع على Railway.", BlockedOnUser=false, PathsToReview=[], ShouldAutoProceed=true)
