from django.db.models import Sum, DateField, Count
from django.db.models.functions import TruncMonth, Cast

from django.views.generic.list import ListView
from django.views.generic.edit import UpdateView
from .forms import ExpenseSearchForm, CategoryForm
from .models import Category, Expense
from .reports import summary_per_category


from django.urls import reverse_lazy
from .models import Category


class ExpenseListView(ListView):
    model = Expense
    paginate_by = 5


    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = object_list if object_list is not None else self.object_list

        form = ExpenseSearchForm(self.request.GET)
        if form.is_valid():
            name = form.cleaned_data.get("name", "").strip()
            date_from = form.cleaned_data.get("date_from")
            date_to = form.cleaned_data.get("date_to")
            categories = form.cleaned_data.get("categories")

            if name:
                queryset = queryset.filter(name__icontains=name)
            if date_from and date_to:
                queryset = queryset.filter(date__range=[date_from, date_to])
            elif date_from:
                queryset = queryset.filter(date__gte=date_from)
            elif date_to:
                queryset = queryset.filter(date__lte=date_to)

            if categories:
                queryset = queryset.filter(category__in=categories)

        sort_by = self.request.GET.get("sort_by")
        if sort_by == "category_asc":
            queryset = queryset.order_by("category")
        elif sort_by == "category_desc":
            queryset = queryset.order_by("-category")
        elif sort_by == "date_asc":
            queryset = queryset.order_by("date")
        elif sort_by == "date_desc":
            queryset = queryset.order_by("-date")

        
        total_amount_spent = queryset.aggregate(total_amount=Sum('amount'))['total_amount']

        summary_per_year_month = queryset.annotate(
            year_month=TruncMonth(Cast('date', output_field=DateField()))
        ).values('year_month').annotate(total_summary=Sum('amount')).order_by('-year_month')

        return super().get_context_data(
            form=form,
            object_list=queryset,
            summary_per_category=summary_per_category(queryset),
            total_amount_spent=total_amount_spent,  
            summary_per_year_month=summary_per_year_month,
            **kwargs
        )


class CategoryListView(ListView):
    model = Category
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.annotate(expense_count=Count('expense'))
        return queryset
    
