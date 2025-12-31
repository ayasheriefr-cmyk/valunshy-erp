import os

template_content = r"""{% extends "admin/base.html" %}
{% load static %}
{% block extrahead %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
    /* Premium Root Variables */
    :root {
        --gold-bright: #FFD700;
        --gold-soft: rgba(212, 175, 55, 0.2);
        --glass-border: rgba(212, 175, 55, 0.3);
        --text-bright: #ffffff;
        --text-dim: #b0b0b0;
    }

    .analytics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin-bottom: 3rem;
    }

    .metric-card {
        padding: 2rem;
        text-align: center;
        position: relative;
        overflow: hidden;
        animation: fadeIn 0.8s ease-out forwards;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
    }

    .metric-card i {
        font-size: 2.5rem;
        margin-bottom: 1.5rem;
        display: block;
        transition: transform 0.3s ease;
    }

    .metric-card:hover i {
        transform: scale(1.2) rotate(10deg);
    }

    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        margin-bottom: 0.5rem;
        font-family: "Outfit", "Inter", sans-serif;
        color: var(--text-bright);
    }

    /* Dark Mode Visibility Fixes */
    body.dark-mode .custom-table, 
    body.dark-mode .glass-card,
    .dashboard-container .glass-card {
        color: var(--text-bright);
    }

    .custom-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0 8px;
        color: var(--text-bright);
    }

    .custom-table th {
        background: rgba(212, 175, 55, 0.15);
        color: var(--gold-bright);
        padding: 15px;
        font-weight: 700;
        border-bottom: 2px solid var(--gold-primary);
    }

    .custom-table td {
        background: rgba(255, 255, 255, 0.03);
        padding: 15px;
        border-top: 1px solid var(--glass-border);
        border-bottom: 1px solid var(--glass-border);
        color: var(--text-bright) !important; /* Ensure visibility in dark mode */
    }

    .custom-table tr:hover td {
        background: rgba(212, 175, 55, 0.08);
    }

    .metric-label {
        color: var(--text-dim);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-size: 0.85rem;
        font-weight: 700;
    }

    .chart-box {
        height: 300px;
        margin-top: 2rem;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .recommendation-item {
        background: rgba(212, 175, 55, 0.08);
        border: 1px solid var(--glass-border);
        border-right: 4px solid var(--gold-primary);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 1.5rem;
        transition: all 0.3s ease;
        color: var(--text-bright);
    }

    .recommendation-item:hover {
        background: rgba(212, 175, 55, 0.15);
        transform: translateX(10px);
    }

    .rec-icon {
        width: 40px;
        height: 40px;
        background: var(--gold-primary);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #000;
        flex-shrink: 0;
    }

    .profit-good { border-color: #4CAF50 !important; }
    .profit-bad { border-color: #ff4b2b !important; }
    .revenue-text { color: #4CAF50 !important; }
    .expense-text { color: #ff6b6b !important; }
    .stone-text { color: #b388ff !important; }
    .gold-text { color: var(--gold-bright) !important; }

    .unit-small { font-size: 1rem; opacity: 0.7; }

    .tahyif-info {
        margin-top: 10px;
        font-weight: 700;
        color: var(--gold-bright);
    }

    .grid-2col {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
    }

    .chart-label-ltr { direction: ltr; text-align: center; }

    .card-spacing {
        margin-top: 30px;
        border: 2px solid var(--gold-primary);
    }
</style>
{% endblock %}

{% block content %}
<div class="dashboard-container">
    <div class="dashboard-header" style="margin-bottom: 2rem;">
        <h1 class="dashboard-title">
            <i class="fa-solid fa-chart-line"></i> {{ title }}
        </h1>
        <form method="get" class="header-actions" style="display: flex; gap: 15px; align-items: center; flex-wrap: wrap; background: rgba(0,0,0,0.2); padding: 15px; border-radius: 12px; border: 1px solid var(--glass-border);">
            <div class="select-wrapper" style="display: flex; gap: 8px; align-items: center;">
                <label style="font-size: 0.9rem; color: var(--gold-bright); font-weight: 600;">نوع التقرير:</label>
                <select name="report_type" class="form-control" style="width: auto; background: #1a1a1a; color: #fff; border: 1px solid var(--gold-primary); border-radius: 8px; padding: 5px 10px;">
                    <option value="monthly" {% if report_type == "monthly" %}selected{% endif %}>شهري</option>
                    <option value="quarterly" {% if report_type == "quarterly" %}selected{% endif %}>ربع سنوي</option>
                    <option value="semi_annual" {% if report_type == "semi_annual" %}selected{% endif %}>نصف سنوي</option>
                    <option value="annual" {% if report_type == "annual" %}selected{% endif %}>سنوي</option>
                </select>
            </div>

            <div class="select-wrapper" style="display: flex; gap: 8px; align-items: center;">
                <label style="font-size: 0.9rem; color: var(--gold-bright); font-weight: 600;">الشهر:</label>
                <select name="month" class="form-control" style="width: auto; background: #1a1a1a; color: #fff; border: 1px solid var(--gold-primary); border-radius: 8px; padding: 5px 10px;">
                    {% for m in month_choices %}<option value="{{ m.value }}" {% if month == m.value %}selected{% endif %}>{{ m.label }}</option>{% endfor %}
                </select>
            </div>

            <div class="select-wrapper" style="display: flex; gap: 8px; align-items: center;">
                <label style="font-size: 0.9rem; color: var(--gold-bright); font-weight: 600;">السنة:</label>
                <select name="year" class="form-control" style="width: auto; background: #1a1a1a; color: #fff; border: 1px solid var(--gold-primary); border-radius: 8px; padding: 5px 10px;">
                    {% for y in year_choices %}<option value="{{ y }}" {% if year == y %}selected{% endif %}>{{ y }}</option>{% endfor %}
                </select>
            </div>

            <button type="submit" class="btn-new-order" style="box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);">
                <i class="fa-solid fa-filter"></i> تحديث التقرير
            </button>
            <button type="button" onclick="window.print()" class="btn-new-order" style="background: rgba(255,255,255,0.05); border: 1px solid var(--glass-border);">
                <i class="fa-solid fa-print"></i> طباعة
            </button>
        </form>
    </div>

    <div class="analytics-grid">
        <div class="glass-card metric_card">
            <i class="fa-solid fa-money-bill-trend-up revenue-text"></i>
            <div class="metric-value revenue-text">{{ total_revenue|floatformat:2 }}</div>
            <div class="metric-label">إجمالي الإيرادات</div>
            <div class="chart-box"><canvas id="revenueChart"></canvas></div>
        </div>

        <div class="glass-card metric_card">
            <i class="fa-solid fa-money-bill-transfer expense-text"></i>
            <div class="metric-value expense_text">{{ total_expenses|floatformat:2 }}</div>
            <div class="metric-label">إجمالي المصروفات</div>
            <div class="chart-box"><canvas id="expenseChart"></canvas></div>
        </div>

        <div class="glass-card metric_card">
            <i class="fa-solid fa-gem stone-text"></i>
            <div class="metric-value stone-text">{{ total_stones_weight|floatformat:2 }} <span class="unit-small">جم</span></div>
            <p class="tahyif-info">يعادل: {{ total_tahyif_gold|floatformat:2 }} جم ذهب (تحييف)</p>
            <div class="metric-label">إجمالي وزن الفصوص</div>
            <div class="chart-box"><canvas id="stoneChart"></canvas></div>
        </div>

        <div class="glass-card metric-card {% if is_profit %}profit-good{% else %}profit-bad{% endif %}">
            <i class="fa-solid fa-scale-balanced gold-text"></i>
            <div class="metric-value gold-text">{{ net_profit|floatformat:2 }}</div>
            <div class="metric-label">صافي الربح / الخسارة</div>
            <div class="chart-box"><canvas id="profitChart"></canvas></div>
        </div>
    </div>

    <div class="grid-2col">
        <div class="glass-card">
            <h3 class="chart-header"><i class="fa-solid fa-handshake"></i> توزيع أرباح الشركاء</h3>
            <div class="table-responsive">
                <table class="custom-table">
                    <thead>
                        <tr>
                            <th>الشريك</th>
                            <th>النسبة (%)</th>
                            <th>حصة الربح (ج.م)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for share in partner_shares %}
                        <tr>
                            <td><b>{{ share.partner.name }}</b></td>
                            <td class="text-center">{{ share.partner.percentage }}%</td>
                            <td class="text-center text-green"><b>{{ share.share|floatformat:2 }}</b></td>
                        </tr>
                        {% empty %}
                        <tr><td colspan="3" class="text-center">لا يوجد شركاء مسجلين</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="glass-card">
            <h3 class="chart-header"><i class="fa-solid fa-stopwatch"></i> كفاءة التشغيل (متوسط الوقت)</h3>
            <div class="table-responsive">
                <table class="custom-table">
                    <thead>
                        <tr>
                            <th>المرحلة (Process)</th>
                            <th>عدد العمليات</th>
                            <th>متوسط الوقت</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for stat in efficiency_data %}
                        <tr>
                            <td>{{ stat.stage }}</td>
                            <td class="text-center">{{ stat.count }}</td>
                            <td class="chart-label-ltr">{{ stat.avg_duration }}</td>
                        </tr>
                        {% empty %}
                        <tr><td colspan="3" class="text-center">لا توجد بيانات تشغيل لهذا الشهر</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="glass-card" style="margin-top: 20px;">
            <h3 class="chart-header"><i class="fa-solid fa-gem"></i> تحليل استخدام الأحجار (Stone Usage)</h3>
            <div class="table-responsive">
                <table class="custom-table">
                    <thead>
                        <tr>
                            <th>نوع الحجر</th>
                            <th>عدد مرات الاستخدام</th>
                            <th>إجمالي الكمية (قيراط)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for stone in stone_usage %}
                        <tr>
                            <td><b>{{ stone.stone__name }}</b></td>
                            <td class="text-center">{{ stone.usage_count }}</td>
                            <td class="text-center" style="color: var(--gold-bright); font-weight: 700;">{{ stone.total_qty|floatformat:3 }}</td>
                        </tr>
                        {% empty %}
                        <tr><td colspan="3" class="text-center">لا توجد بيانات استخدام أحجار لهذا الشهر</td></tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="glass-card card-spacing" style="border: 2px solid var(--gold-primary); background: rgba(212, 175, 55, 0.02); margin-top: 3rem;">
        <h3 class="chart-header gold-text" style="font-size: 1.5rem; border-bottom: 2px solid var(--glass-border); padding-bottom: 15px;">
            <i class="fa-solid fa-wand-magic-sparkles"></i> رؤية الذكاء الاصطناعي وخطة الإنتاج (AI Production Plan)
        </h3>
        <div style="padding: 20px;">
            <div class="grid-2col" style="grid-template-columns: 1fr 1.5fr;">
                <!-- Recommendations Column -->
                <div>
                    <h4 style="margin-bottom: 20px; color: var(--gold-bright);"><i class="fa-solid fa-lightbulb"></i> توجيهات استراتيجية:</h4>
                    {% if recommendations %}
                    <div style="display: flex; flex-direction: column; gap: 15px;">
                        {% for rec in recommendations %}
                        <div class="recommendation-item">
                            <div class="rec-icon"><i class="fa-solid fa-check"></i></div>
                            <div style="font-size: 1rem; font-weight: 600; line-height: 1.5;">{{ rec }}</div>
                        </div>
                        {% endfor %}
                    </div>
                    {% else %}<p class="text-muted">لا توجد توصيات متاحة حالياً.</p>{% endif %}
                </div>

                <!-- Production Plan Column -->
                <div>
                    <h4 style="margin-bottom: 20px; color: #4CAF50;"><i class="fa-solid fa-calendar-check"></i> خطة الإنتاج المقترحة {{ production_plan.0.period|default:"" }}:</h4>
                    <div class="table-responsive">
                        <table class="custom-table">
                            <thead>
                                <tr>
                                    <th>الصنف المستهدف</th>
                                    <th>الإنتاج السابق</th>
                                    <th style="color: var(--gold-bright);">الهدف الجديد</th>
                                    <th style="color: #4CAF50;">الربح المتوقع</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for plan in production_plan %}
                                <tr>
                                    <td><b>{{ plan.item }}</b></td>
                                    <td class="text-center">{{ plan.current_count }}</td>
                                    <td class="text-center" style="font-weight: 800; font-size: 1.1rem; color: var(--gold-bright);">{{ plan.target_count }}</td>
                                    <td class="text-center text-green"><b>{{ plan.expected_profit|floatformat:2 }}</b></td>
                                </tr>
                                {% empty %}
                                <tr><td colspan="4" class="text-center">يرجى إدخال بيانات مبيعات كافية لتوليد الخطة.</td></tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {% if top_products %}
            <div style="margin-top: 40px; padding-top: 30px; border-top: 1px dashed var(--glass-border);">
                <h4 style="margin-bottom: 25px; color: var(--gold-bright);"><i class="fa-solid fa-trophy"></i> تحليل الربحية حسب الصنف (الأكثر تأثيراً):</h4>
                <div class="table-responsive">
                    <table class="custom-table" style="font-size: 1rem;">
                        <thead>
                            <tr>
                                <th>الصنف / الموديل</th>
                                <th>عدد القطع المباعة</th>
                                <th>إجمالي الربح المحقق</th>
                                <th style="color: var(--gold-bright);">متوسط ربح القطعة</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for item in top_products %}
                            <tr>
                                <td><b>{{ item.0 }}</b></td>
                                <td class="text-center">{{ item.1.count }}</td>
                                <td class="text-center text-green"><b>{{ item.1.total_profit|floatformat:2 }}</b></td>
                                <td class="text-center" style="font-weight: 700; color: var(--gold-bright);">{{ item.1.avg_profit|floatformat:2 }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<script>
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { display: false }, y: { display: false } },
        elements: { line: { tension: 0.4 }, point: { radius: 0 } }
    };

    const setupChart = (id, color, val) => {
        new Chart(document.getElementById(id), {
            type: 'line',
            data: {
                labels: ['1', '2', '3', '4', '5'],
                datasets: [{
                    data: [0, val*0.4, val*0.7, val*0.9, val],
                    borderColor: color,
                    fill: true,
                    backgroundColor: color + '1A'
                }]
            },
            options: chartOptions
        });
    };

    setupChart('revenueChart', '#4CAF50', Number("{{ total_revenue|default:0 }}"));
    setupChart('expenseChart', '#ff6b6b', Number("{{ total_expenses|default:0 }}"));
    setupChart('stoneChart', '#b388ff', Number("{{ total_stones_weight|default:0 }}"));
    setupChart('profitChart', '#FFD700', Number("{{ net_profit|default:0 }}"));
</script>
{% endblock %}
"""

template_path = r"C:\Users\COMPU LINE\Desktop\mm\final\gold\templates\finance\monthly_analytics_report.html"

with open(template_path, "w", encoding="utf-8") as f:
    f.write(template_content)

print("Template updated successfully with correct syntax and encoding.")
