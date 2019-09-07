from django.urls import path
from . import views

app_name = "fortnox"

urlpatterns = [

 path("",views.indexView.as_view(),name="index"),
 path("sync/",views.sync_view,name="sync"),
 path("article/post",views.post_article_view,name="post_article"),
 path("article/update/",views.update_article_view,name="update_article"),
 path("article/quick_update_article/<str:article_number>",views.update_article_view,name="quick_update_article"),
 path("invoice/create",views.create_invoice_view,name="create_invoice"),
 path("invoice/bookkeep",views.bookkeep_invoice_view,name="bookkeep_invoice"),
 path("invoice/all/<str:page>",views.invoices_view,name="all_invoices"),
 path("invoice/quick_bookkeep/<str:document_number>",views.bookkeep_invoice_view,name="quick_bookkeep"),
 path("invoice/last_synced/",views.last_synced_invoice_view,name="last_synced"),
 path("articles/all/<str:page>",views.articles_view,name="all_articles"),
 # path('<str:username>/post/<int:pk>/',views.userPostDetailView.as_view(),name="user_post_detail"),
 # path("<int:pk>/unsave/",views.postUnsaveView.as_view(),name="unsave"),
 # path('<int:pk>/save_for_future/',views.postSaveView.as_view(),name="save_for_future"),
 # path("all/",views.postListView.as_view(),name="post_list"),
 # path('<int:pk>/',views.PostDetailView.as_view(),name="post_detail"),
 # path("<str:username>/new/",views.CreatePostView.as_view(),name="create_post"),
 # path('<int:pk>/edit/',views.PostUpdateView.as_view(),name="edit_post"),
 # path('<str:username>/<int:pk>/delete/',views.PostDeleteView.as_view(),name="delete_post"),
 # path("<str:username>/saved/",views.savedListView.as_view(),name="view_saved"),
 # path('<int:pk>/comment/',views.add_comment_to_post,name="add_comment_to_post"),
 # path('<int:pk>/clap/',views.postClapView.as_view(),name="clap"),
 # path('cartegory/<str:name>/',views.cartegoryView.as_view(),name="cartegory"),
 # path('<int:pk>/publish/',views.post_publish,name="post_publish"),
 # path('<int:pk>/unpublish/',views.post_unpublish,name="post_unpublish"),
 # path('join_cartegory/<int:pk>/',views.join_cartegory_view,name="join_cartegory"),
 # path('leave_cartegory/<int:pk>/',views.leave_cartegory_view,name="leave_cartegory"),

]
