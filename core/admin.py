from django.contrib import admin

from .models import (
    CompanyInfo,
    ContactEmployee,
    FAQ,
    NewsArticle,
    PartnerCompany,
    PrivacyPolicy,
    PromoCode,
    Review,
    Vacancy,
)


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')
    search_fields = ('title', 'text')


@admin.register(PartnerCompany)
class PartnerCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'website', 'description')


@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'published_at', 'created_at')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title', 'summary', 'body')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'created_at')
    search_fields = ('question', 'answer')


@admin.register(ContactEmployee)
class ContactEmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'phone', 'email')
    search_fields = ('full_name', 'position', 'phone', 'email')


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')


@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('title', 'updated_at')
    search_fields = ('title', 'text')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'rating', 'is_published', 'created_at')
    list_filter = ('rating', 'is_published', 'created_at')
    search_fields = ('author_name', 'text')


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'starts_at', 'ends_at', 'is_active')
    list_filter = ('is_active', 'starts_at', 'ends_at')
    search_fields = ('code', 'description')
