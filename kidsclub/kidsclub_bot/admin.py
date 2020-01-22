from django.contrib import admin
from .models import Person, PersonKid, BotMessage, InviteIntent, Location, PersonMeeting


class BookclubAdminSite(admin.AdminSite):
    site_header = 'Детский клуб'


class PersonMeetingInline(admin.StackedInline):
    model = PersonMeeting
    fk_name = 'from_person'
    can_delete = False
    fields = ('to_person', 'rate', 'review')
    readonly_fields = ('to_person', 'rate', 'review')
    extra = 0


class PersonKidInline(admin.StackedInline):
    model = PersonKid
    fk_name = 'person'
    readonly_fields = ('kid_seg_number', )
    can_delete = False
    extra = 0


class PersonAdmin(admin.ModelAdmin):
    list_display = (
        'tg_id', 'tg_username', 'username', 'location',
        'good_review', 'bad_review', 'not_met_review',
        'is_blocked'
    )
    list_filter = ('is_blocked', )
    list_per_page = 15
    inlines = [PersonMeetingInline, PersonKidInline]

    def good_review(self, person):
        return (
            PersonMeeting.objects.filter(
                from_person=person,
                rate=PersonMeeting.MeetingRate.GOOD
            ).count()
        )

    def bad_review(self, person):
        return (
            PersonMeeting.objects.filter(
                from_person=person,
                rate=PersonMeeting.MeetingRate.BAD
            ).count()
        )

    def not_met_review(self, person):
        return (
            PersonMeeting.objects.filter(
                from_person=person,
                rate=PersonMeeting.MeetingRate.NOT_MET
            ).count()
        )


admin_site = BookclubAdminSite(name='bookclub_admin')
admin_site.register(Person, PersonAdmin)
admin_site.register(Location)
admin_site.register(BotMessage)
admin_site.register(InviteIntent)
admin_site.register(PersonMeeting)
admin_site.register(PersonKid)
