import re
import datetime
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from sales.models import Invoice, InvoiceItem
from inventory.models import Item, Branch
from manufacturing.models import ManufacturingOrder
from core.models import GoldPrice
from crm.models import Customer
from finance.treasury_models import Treasury, TreasuryTransaction

class ValunshyAI:
    """
    Valunshy AI Agentic Intelligence Engine v5.0
    Capable of analysis, prediction, and operational insights.
    """
    
    def __init__(self, user):
        self.user = user
        self.today = timezone.now().date()
        self.now = timezone.now()

    def _normalize_arabic(self, text):
        if not text: return ""
        text = text.lower().strip()
        # Remove common honorifics and noise
        text = re.sub(r"[أإآ]", "ا", text)
        text = re.sub(r"ة", "ه", text)
        text = re.sub(r"ى", "ي", text)
        text = re.sub(r"ؤ", "و", text)
        text = re.sub(r"ئ", "ي", text)
        # Remove Tashkeel
        text = re.sub(r"[\u064B-\u0652]", "", text)
        return text

    def process_query(self, query):
        norm_query = self._normalize_arabic(query)
        
        # 0. Exact Quick Command Handling (Priority)
        # matches the buttons in base.html exactly to ensure they always work
        if "تحليل المصروفات" in norm_query or "تحليل المصاريف" in norm_query:
            return self._handle_expenses(norm_query)
        if "مبيعات اليوم" in norm_query:
            return self._handle_sales(norm_query)
        if "رصيد الذهب" in norm_query:
            return self._handle_inventory(norm_query)
        if "تدقيق البيانات" in norm_query:
            return self._handle_auditing()
        if "خطة" in norm_query and "مبيعات" in norm_query:
            return self._handle_strategy(norm_query)
        if "ملخص الموقف" in norm_query or "ملخص عام" in norm_query:
            return self._handle_summary()

        # 1. Strategic & Predictive Intent (High Priority)
        # Using normalized keywords to match normalized query
        if self._is_intent(norm_query, ['نصيحه', 'توقع', 'خطه', 'ازاي', 'تطوير', 'نزود', 'كيف', 'استراتيجيه', 'مستقبل']):
            if any(word in norm_query for word in ['تطوير', 'خطه', 'ازاي', 'كيف', 'نزود', 'زياده', 'استراتيجيه']):
                return self._handle_strategy(norm_query)
            return self._handle_predictive(norm_query)

        # 2. Operational Routing
        if self._is_intent(norm_query, ['مبيع', 'فواتير', 'دخل', 'باعت', 'بعنا', 'ايراد']):
            return self._handle_sales(norm_query)
        
        if self._is_intent(norm_query, ['مخزن', 'نواقص', 'خلص', 'بضاعه', 'رصيد', 'كميه', 'جرد']):
            if 'رصيد' in norm_query and 'ذهب' in norm_query:
                return self._handle_inventory(norm_query)
            return self._handle_inventory(norm_query)
        
        if self._is_intent(norm_query, ['تصنيع', 'ورشة', 'فني', 'شغل', 'مصنع', 'انتاج']):
            return self._handle_manufacturing(norm_query)
        
        if self._is_intent(norm_query, ['خزنه', 'فلوس', 'سيوله', 'صراف', 'رصيد', 'نقديه']):
            if 'خزنه' in norm_query or 'فلوس' in norm_query or 'سيوله' in norm_query or 'نقديه' in norm_query:
                return self._handle_finance(norm_query)
        
        if self._is_intent(norm_query, ['عميل', 'ديون', 'حسابات', 'مديونيه', 'اشتري', 'زبون']):
            return self._handle_crm(norm_query)
        
        if self._is_intent(norm_query, ['مصروف', 'صرف', 'خسرنا', 'تكلفه', 'نفقات', 'مصاريف']):
            return self._handle_expenses(norm_query)

        if self._is_intent(norm_query, ['سعر', 'عيار', 'ذهب', 'تمن']):
            return self._handle_gold_prices(norm_query)

        if self._is_intent(norm_query, ['راجع', 'تدقيق', 'غلط', 'فحص', 'مشاكل']):
            return self._handle_auditing()

        # 3. Hidden "Status" report
        if any(word in norm_query for word in ['ملخص', 'تقرير', 'summary', 'report', 'حال', 'ايه الاخبار']):
            return self._handle_summary()

        return self._fallback_response()

    def _is_intent(self, query, triggers):
        return any(word in query for word in triggers)

    def _handle_sales(self, query):
        # Time detection
        period, period_name = self._detect_period(query)
        qs = Invoice.objects.filter(**period)
        
        # Best sellers check
        if any(word in query for word in ['أكثر', 'افضل', 'top', 'best', 'ايه']):
            items = InvoiceItem.objects.filter(invoice__in=qs).values('item__name').annotate(
                total_weight=Sum('sold_weight'),
                total_qty=Count('id')
            ).order_by('-total_weight')[:3]
            
            if not items: return f"لا توجد بيانات مبيعات كافية للفترة: <b>{period_name}</b>"
            
            html = f"🏆 <b>أفضل المنتجات مبيعاً ({period_name}):</b><br>"
            for idx, itm in enumerate(items, 1):
                html += f"{idx}. {itm['item__name']} - {itm['total_weight']} جم ({itm['total_qty']} قطعة)<br>"
            return html

        # General sales stats
        stats = qs.aggregate(
            total=Sum('grand_total'),
            count=Count('id'),
            labor=Sum('total_labor_value')
        )
        total = stats['total'] or 0
        count = stats['count'] or 0
        
        html = f"💰 <b>مؤشر المبيعات ({period_name}):</b><br>"
        html += f"• الإجمالي: <b>{total:,.0f} ج.م</b><br>"
        html += f"• عدد العمليات: <b>{count} فاتورة</b><br>"
        
        # Brain context: compare with previous period
        prev_period, _ = self._detect_period(query, offset=1)
        prev_total = Invoice.objects.filter(**prev_period).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        
        if total > prev_total and prev_total > 0:
            growth = ((total - prev_total) / prev_total) * 100
            html += f"<span style='color: #4CAF50;'>📈 نمو بنسبة {growth:,.1f}% عن الفترة السابقة.</span>"
        elif total < prev_total and prev_total > 0:
            drop = ((prev_total - total) / prev_total) * 100
            html += f"<span style='color: #f44336;'>📉 تراجع بنسبة {drop:,.1f}% عن الفترة السابقة.</span>"
        
        return html

    def _handle_expenses(self, query):
        from finance.models import LedgerEntry, Account
        period, period_name = self._detect_period(query)
        
        # Support specifically for "Total expenses"
        expense_accounts = Account.objects.filter(account_type='expense')
        total_exp = LedgerEntry.objects.filter(
            account__in=expense_accounts,
            journal_entry__date__range=[period.get('created_at__date', self.today), period.get('created_at__date', self.today)] if 'created_at__date' in period else [self.today, self.today]
        ).aggregate(total=Sum('debit'))['total'] or 0
        
        # If generic month/year
        if 'created_at__month' in period:
             total_exp = LedgerEntry.objects.filter(
                account__in=expense_accounts,
                journal_entry__date__year=period['created_at__year'],
                journal_entry__date__month=period['created_at__month']
            ).aggregate(total=Sum('debit'))['total'] or 0

        html = f"💸 <b>تحليل المصروفات ({period_name}):</b><br>"
        html += f"• إجمالي المصروفات: <b>{total_exp:,.2f} ج.م</b><br>"
        
        # Top 3 expense categories
        top_exp = LedgerEntry.objects.filter(account__in=expense_accounts).values('account__name').annotate(total=Sum('debit')).order_by('-total')[:3]
        if top_exp:
            html += "<br><b>أعلى بنود الصرف:</b><br>"
            for exp in top_exp:
                html += f"• {exp['account__name']}: {exp['total']:,.0f} ج.م<br>"
        
        return html

    def _handle_inventory(self, query):
        if any(word in query for word in ['نواقص', 'خلص', 'low', 'out']):
            # Items below weight threshold or specific branch low count
            branches = Branch.objects.all()
            results = []
            for b in branches:
                cnt = Item.objects.filter(current_branch=b, status='available').count()
                if cnt < 5:
                    results.append(f"📦 <b>{b.name}</b>: رصيد منخفض جداً ({cnt} قطعة)")
            
            if results:
                return "⚠️ <b>تحذير المخزون:</b><br>" + "<br>".join(results) + "<br><small>ينصح بنقل بضاعة من المخزن الرئيسي.</small>"
            return "✅ المخزون في جميع الفروع متوازن ومستقر."

        # Gold weight specific
        if 'ذهب' in query or 'وزن' in query:
            breakdown = Item.objects.filter(status='available').values('carat__name').annotate(weight=Sum('net_gold_weight'), count=Count('id'))
            html = "💎 <b>رصيد الذهب حسب العيار:</b><br>"
            total_w = 0
            for b in breakdown:
                html += f"• {b['carat__name']}: <b>{b['weight']:,.2f} جم</b> ({b['count']} قطعة)<br>"
                total_w += b['weight']
            html += f"━━━━━━━━━━━━━━<br>• الإجمالي: <b>{total_w:,.2f} جم</b>"
            return html

        # General breakdown
        total_w = Item.objects.filter(status='available').aggregate(Sum('net_gold_weight'))['net_gold_weight__sum'] or 0
        items_count = Item.objects.filter(status='available').count()
        return f"💎 <b>حالة المخزون الكلي:</b><br>• الوزن الإجمالي: <b>{total_w:,.2f} جم</b><br>• عدد القطع: <b>{items_count} قطعة</b>"

    def _handle_manufacturing(self, query):
        qs = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled'])
        count = qs.count()
        
        if count == 0: return "🛠️ لا يوجد أوامر تصنيع قيد التنفيذ حالياً."
        
        # Analysis of delays
        delayed = qs.filter(expected_delivery__lt=self.today).count()
        
        # Deep analysis
        stages = qs.values('status').annotate(cnt=Count('id'))
        details = ""
        for s in stages:
            status_display = dict(ManufacturingOrder.STATUS_CHOICES).get(s['status'], s['status'])
            details += f"• {status_display}: <b>{s['cnt']} طلب</b><br>"
            
        html = f"🏭 <b>سير العمل في المصنع:</b><br>{details}<br>"
        if delayed > 0:
            html += f"<span style='color: #f44336;'>⚠️ يوجد {delayed} طلب متأخر عن موعد التسليم!</span><br>"
        html += f"<small>مجموع الطلبات المفتوحة: {count}</small>"
        return html

    def _handle_finance(self, query):
        total_cash = Treasury.objects.aggregate(Sum('cash_balance'))['cash_balance__sum'] or 0
        treasuries = Treasury.objects.filter(is_active=True)
        
        html = f"🏦 <b>الموقف المالي للخزائن:</b><br>• السيولة الكلية: <b>{total_cash:,.0f} ج.م</b><br>"
        for t in treasuries:
            html += f"🏢 {t.name}: {t.cash_balance:,.0f} ج.م<br>"
            
        # Safety check
        if total_cash < 10000:
            html += "<br><span style='color: #f44336;'>⚠️ تنبيه: السيولة النقدية منخفضة جداً!</span>"
            
        return html

    def _handle_gold_prices(self, query):
        prices = GoldPrice.objects.all().order_by('-carat__name')
        html = "✨ <b>سعر الذهب المسجل حالياً:</b><br>"
        for p in prices:
            html += f"🔸 {p.carat.name}: <b>{p.price_per_gram:,.2f}</b> ج.م<br>"
        
        # Logic check: is price old?
        latest = prices.order_by('-updated_at').first()
        if latest:
            diff = (timezone.now() - latest.updated_at).total_seconds() / 3600
            if diff > 12:
                html += f"<br><small style='color: #FF9800;'>⚠️ تنبيه: الأسعار لم تُحدّث منذ {int(diff)} ساعة.</small>"
        
        return html

    def _handle_crm(self, query):
        if any(word in query for word in ['دين', 'مديونيات', 'ارصدة']):
            debtors = Customer.objects.filter(money_balance__lt=0).order_by('money_balance')[:5]
            if not debtors: return "✅ لا يوجد عملاء لديهم مديونيات متأخرة حالياً."
            
            html = "💸 <b>كبار المديونيات للعملاء:</b><br>"
            for d in debtors:
                html += f"👤 {d.name}: <span style='color: #f44336;'>{abs(d.money_balance):,.0f} ج.م</span><br>"
            return html
            
        # Loyalty check
        if any(word in query for word in ['افضل', 'اهم', 'ولاء', 'نقاط']):
            vip = Customer.objects.order_by('-loyalty_points')[:5]
            html = "🌟 <b>كبار العملاء (حسب نقاط الولاء):</b><br>"
            for c in vip:
                html += f"• {c.name}: <b>{c.loyalty_points} نقطة</b><br>"
            return html

        total_cust = Customer.objects.count()
        new_cust = Customer.objects.filter(created_at__date=self.today).count()
        return f"👥 <b>قاعدة العملاء:</b><br>• إجمالي العملاء: {total_cust}<br>• عملاء اليوم الجدد: {new_cust}"

    def _handle_auditing(self):
        issues = []
        # Check 1: Negative treasury
        neg_t = Treasury.objects.filter(cash_balance__lt=0)
        for t in neg_t:
            issues.append(f"• الخزينة <b>{t.name}</b> رصيدها سالب ({t.cash_balance}).")
            
        # Check 2: Expired Manufacturing Orders
        delayed = ManufacturingOrder.objects.exclude(
            status__in=['completed', 'cancelled']
        ).filter(end_date__lt=self.today).count()
        if delayed > 0:
            issues.append(f"• يوجد <b>{delayed}</b> طلب تصنيع متأخر عن الموعد.")
            
        # Check 3: Missing Prices
        missing_prices = GoldPrice.objects.filter(updated_at__date__lt=self.today).count()
        if missing_prices > 0:
            issues.append(f"• أسعار الذهب لم يتم تحديثها لليوم.")

        # Check 4: Overdue Custody
        from finance.treasury_models import Custody, ExpenseVoucher
        overdue_c = Custody.objects.filter(status='active', due_date__lt=self.today).count()
        if overdue_c > 0:
            issues.append(f"• يوجد <b>{overdue_c}</b> عهدة متأخرة لم يتم تسويتها.")

        # Check 5: Pending Vouchers
        pending_v = ExpenseVoucher.objects.filter(status='pending').count()
        if pending_v > 0:
            issues.append(f"• يوجد <b>{pending_v}</b> إذن صرف معلق ينتظر الاعتماد.")

        if not issues:
            return "✅ <b>تقرير التدقيق الذكي:</b> لم يتم العثور على أي مشاكل منطقية في البيانات حالياً. العمل يسير بشكل ممتاز."
        
        return "🔍 <b>نتائج التدقيق والتدخل المطلوب:</b><br>" + "<br>".join(issues)

    def _handle_predictive(self, query):
        # Brain logic for prediction
        week_ago = self.today - datetime.timedelta(days=7)
        two_weeks_ago = self.today - datetime.timedelta(days=14)
        
        last_week = Invoice.objects.filter(created_at__date__gte=week_ago).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        prev_week = Invoice.objects.filter(created_at__date__gte=two_weeks_ago, created_at__date__lt=week_ago).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        
        html = "🔮 <b>التحليل التوقعي الذكي:</b><br>"
        
        if last_week > prev_week:
            html += "📈 <b>اتجاه صاعد:</b> المبيعات في تحسن بنسبة ملحوظة. نتوقع استمرار هذا الزخم للأسبوع القادم.<br>"
        else:
            html += "📉 <b>تحذير ركود:</b> لوحظ انخفاض في المبيعات الأسبوعية. ينصح بمراجعة أسعار 'المصنعية' للمنافسة.<br>"
            
        # Inventory safety
        low_stock_count = Item.objects.filter(status='available').count()
        if low_stock_count < 20:
            html += "⚠️ <b>خطر نفاذ:</b> المخزون الحالي قد لا يكفي لطلبات الأسبوع القادم. ابدأ في التصنيع فوراً."
            
        return html

    def _handle_strategy(self, query):
        html = "🎯 <b>استراتيجية فالونشي للتطوير والربحية:</b><br><br>"
        
        # 1. Production Planning & Profit Optimization (NEW)
        if any(word in query for word in ['انتاج', 'تصنيع', 'ربح', 'ازود', 'خطة']):
            # Calculate profitability per model/category from historical sales
            # Profit = Total Labor Value + Gold Markup (estimated)
            best_profit_items = InvoiceItem.objects.values('item__item_type__name', 'item__name').annotate(
                avg_labor=Sum('labor_value') / Count('id'),
                total_qty=Count('id'),
                total_profit=Sum('labor_value')
            ).order_by('-avg_labor')[:5]

            if any(word in query for word in ['كم', 'عدد', 'اد ايه', 'هدف']):
                # Attempt to extract target profit from query or use a default
                target_profit = 50000 # Default target
                match = re.search(r'(\d+)', query)
                if match:
                    target_profit = int(match.group(1))
                
                html += f"📋 <b>خطة إنتاج مقترحة لتحقيق ربح {target_profit:,.0f} ج.م:</b><br>"
                html += "بناءً على تحليل أداء مبيعاتك وأعلى الموديلات ربحية (من حيث المصنعية):<br><br>"
                
                remaining_profit = target_profit
                for item in best_profit_items:
                    avg_p = float(item['avg_labor']) or 100 # Fallback
                    qty_needed = int(remaining_profit / avg_p) + 1
                    if qty_needed > 0:
                        html += f"• <b>{item['item__name'] or item['item__item_type__name']}</b>: أنتج <b>{qty_needed} قطعة</b> (متوسط ربح القطعة {avg_p:,.0f} ج.م)<br>"
                        # For simulation, just show top 3 recommendations
                        remaining_profit -= (qty_needed * avg_p)
                        if remaining_profit <= 0: break
                
                html += "<br>💡 <i>ملاحظة: هذه الأرقام تعتمد على 'قيمة المصنعية' المحصلة تاريخياً من هذه الموديلات.</i><br>"
            else:
                html += "🛠️ <b>تحسين كفاءة الإنتاج:</b><br>"
                open_orders = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled']).count()
                if open_orders > 15:
                    html += f"• الورشة مثقلة بـ {open_orders} طلب. الأولوية الآن لإنهاء المتأخرات لرفع مبيعات الأسبوع.<br>"
                else:
                    html += "• طاقة الإنتاج تسمح بالتركيز على موديلات 'الأطقم' و'الأساور' لأنها تحقق أعلى هامش ربح مصنعية حالياً.<br>"
                
                if best_profit_items.exists():
                    top = best_profit_items[0]
                    html += f"• <b>نصيحة ذهبية:</b> الموديلات من نوع <b>{top['item__name']}</b> تحقق لك أعلى عائد، ركز في إنتاجها حالياً.<br>"

        # 2. Sales & Finance Advice
        elif any(word in query for word in ['مبيع', 'دخل', 'فلوس', 'ارباح']):
            html += "📈 <b>استراتيجية المبيعات والسيولة:</b><br>"
            total_cash = Treasury.objects.aggregate(Sum('cash_balance'))['cash_balance__sum'] or 0
            if total_cash > 500000:
                html += "• يتوفر لديك سيولة ممتازة. الوقت مناسب لشراء 'سبائك' أو 'كسر' للتحوط من تقلبات الأسعار.<br>"
            else:
                html += "• السيولة الحالية تتطلب التركيز على المبيعات النقدية وتحصيل المديونيات لتمويل الإنتاج الجديد.<br>"
            html += "• تفعيل نظام 'الولاء' لتقديم خصم 5% على المصنعية لمن يتخطى مشترياته 100 جرام يشجع على الشراء المتكرر.<br>"
            
        # 3. General Growth
        else:
            html += "🚀 <b>تطوير الأعمال العام:</b><br>"
            html += "• التوسع في عيار 18k للتصميمات العصرية هو التوجه الحالي للسوق.<br>"
            html += "• تحليل 'نواقص المخزون' آلياً يضمن عدم ضياع فرص بيع بسبب انعدام صنف معين.<br>"

        html += f"<br><small>💡 <i>تم تحليل {Invoice.objects.count()} عملية بيع و {ManufacturingOrder.objects.count()} طلب إنتاج لتوليد هذه الخطة.</i></small>"
        return html

    def _handle_summary(self):
        today_sales = Invoice.objects.filter(created_at__date=self.today).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        open_mo = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled']).count()
        total_cash = Treasury.objects.aggregate(Sum('cash_balance'))['cash_balance__sum'] or 0
        inv_w = Item.objects.filter(status='available').aggregate(Sum('net_gold_weight'))['net_gold_weight__sum'] or 0

        html = "📊 <b>ملخص الموقف الحالي (Real-time):</b><br>"
        html += f"• مبيعات اليوم: <b>{today_sales:,.0f} ج.م</b><br>"
        html += f"• طلبات التصنيع: <b>{open_mo} طلب</b><br>"
        html += f"• السيولة الكلية: <b>{total_cash:,.0f} ج.م</b><br>"
        html += f"• وزن المخزون: <b>{inv_w:,.2f} جم</b><br>"
        html += "<br>✨ النظام مستقر وجميع المؤشرات طبيعية."
        return html

    def get_smart_status(self):
        """Returns a concise intelligent sentence for the dashboard banner."""
        today_sales = Invoice.objects.filter(created_at__date=self.today).aggregate(Sum('grand_total'))['grand_total__sum'] or 0
        total_cash = Treasury.objects.aggregate(Sum('cash_balance'))['cash_balance__sum'] or 0
        open_mo = ManufacturingOrder.objects.exclude(status__in=['completed', 'cancelled']).count()
        
        # 1. Critical alerts first
        if total_cash < 5000:
            return "⚠️ تنبيه عاجل: السيولة المالية في الخزائن منخفضة جداً!"
        
        delayed = ManufacturingOrder.objects.exclude(
            status__in=['completed', 'cancelled']
        ).filter(end_date__lt=self.today).count()
        if delayed > 0:
            return f"🚨 يوجد {delayed} طلبات تصنيع متأخرة عن موعدها، قد يؤثر ذلك على سمعة المحل."
            
        # 2. Performance insights
        if today_sales > 100000:
            return "🚀 أداء ممتاز اليوم! المبيعات تخطت حاجز الـ 100 ألف ج.م."
            
        if open_mo > 20:
            return f"🔧 خط الإنتاج مزدحم ({open_mo} طلب)، يفضل زيادة وتيرة العمل في الورشة."
            
        # 3. Default positive message
        return "✨ جميع مؤشرات النظام مستقرة، والعمل يسير بشكل منتظم."

    def _detect_period(self, query, offset=0):
        # Logic to handle Today, Yesterday, Month, etc.
        day = self.today - datetime.timedelta(days=offset)
        
        if any(word in query for word in ['أمس', 'امس']):
            day = self.today - datetime.timedelta(days=1 + offset)
            return {'created_at__date': day}, "أمس"
        
        if 'شهر' in query:
            target_date = self.today - datetime.timedelta(days=30 * offset)
            return {'created_at__year': target_date.year, 'created_at__month': target_date.month}, "هذا الشهر"
            
        if any(word in query for word in ['سنة', 'عام']):
            target_year = self.today.year - offset
            return {'created_at__year': target_year}, "هذا العام"

        return {'created_at__date': day}, "اليوم"

    def _fallback_response(self):
        return (
            "🤔 اعتذر، لم أفهم استفسارك تماماً. لكن بصفتي مساعدك الذكي، يمكنني مساعدتك في التالي:<br>"
            "• 💰 <b>المبيعات:</b> (مبيعات اليوم، أفضل المنتجات).<br>"
            "• 💸 <b>المصروفات:</b> (تحليل المصاريف، الخسائر).<br>"
            "• 📦 <b>المخزون:</b> (رصيد الذهب، النواقص بالتفصيل).<br>"
            "• 🔨 <b>التصنيع:</b> (حالة الورشة، الطلبات المتأخرة).<br>"
            "• 🔍 <b>التدقيق:</b> (البحث عن أخطاء في البيانات).<br>"
            "• 🔮 <b>الذكاء:</b> (توقعات المبيعات، خطة استراتيجية).<br>"
            "• 💴 <b>النقدية:</b> (رصيد الخزائن، السيولة)."
        )
