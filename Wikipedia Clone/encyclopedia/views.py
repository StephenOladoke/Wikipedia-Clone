from django.http.response import HttpResponse
import markdown2
import random
from django import forms
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.core.files.storage import default_storage
from . import util

# homepage
def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries(),
        "form": SearchForm()
    })
    
# searchbar for entries 
class SearchForm(forms.Form):
    query = forms.CharField(label="",
        widget=forms.TextInput(attrs={'placeholder': 'Search Encyclopedia', 'style': 'width:98%'}))


# enter title form for a new entry page
class NewPageForm(forms.Form):
    title = forms.CharField(label="", widget=forms.TextInput(attrs={
            'placeholder': 'Title', 'style': 'width:20%'}))
    data = forms.CharField(label="", widget=forms.Textarea(attrs={
        'id': 'new-entry'}))


# edit for entry page
class EditPageForm(forms.Form):
    title = forms.CharField(label="", widget=forms.TextInput(attrs={}))
    data = forms.CharField(label="", widget=forms.Textarea(attrs={
        'id': 'edit-entry'}))

# page for each entry
def entry(request, title):
    entry = util.get_entry(title) # Markdown content for the given title
    if entry is None:  # If not, show an error page
        return render(request, "encyclopedia/error.html", {
            "title": title,
            "form": SearchForm()
        })

    # If the above variable isn't None, return the entry page
    else:
        return render(request, "encyclopedia/entry.html", {
            "title": title,
            "entry": markdown2.markdown(entry),
            "entry_raw": entry,
            "form": SearchForm()
        })


# Create django form for new wiki entry/page
def create(request):
    if request.method == "POST":
        new_entry = NewPageForm(request.POST) #Take in the data the user submitted and save it as form
        if new_entry.is_valid(): # find out if form data is valid (server-side)
            title = new_entry.cleaned_data["title"] # get title of new entry
            data = new_entry.cleaned_data["data"]
            entries_all = util.list_entries() # find out if entry exists with title

            # If entry already exists, return or show an error
            for entry in entries_all:
                if entry.lower() == title.lower():
                    return render(request, "encyclopedia/create.html", {
                        "form": SearchForm(),
                        "newPageForm": NewPageForm(),
                        "error": "This entry already exists."
                    })

            new_entry_title = "# " + title  # Added markdown for content of entry
            new_entry_data = "\n" + data # A new line is appended to seperate title from content
            new_entry_content = new_entry_title + new_entry_data # Combine the title and data to store as content
            util.save_entry(title, new_entry_content) # Save the new entry with the title
            entry = util.get_entry(title)

            # Revert back to page for the newly created entry
            return render(request, "encyclopedia/entry.html", {
                "title": title,
                "entry": markdown2.markdown(entry),
                "form": SearchForm()
            })

    # Default values
    return render(request, "encyclopedia/create.html", {
        "form": SearchForm(),
        "newPageForm": NewPageForm()
    })

    # entry search
def search(request):
    if request.method == "POST":
        entries_found = []  #List of entries that match query
        entries_all = util.list_entries()  #All entries
        form = SearchForm(request.POST)  #Take in the data the user submitted and save it as form
        
        if form.is_valid(): # Check if form data is valid (server-side)
            query = form.cleaned_data["query"]  # get the query from the 'cleaned' version of form data to search entries/pages
            for entry in entries_all:
                if query.lower() == entry.lower():
                    title = entry
                    entry = util.get_entry(title)
                    return HttpResponseRedirect(reverse("entry", args=[title ])) # Redirect user to the page If an entry exists
        
                if query.lower() in entry.lower():
                    entries_found.append(entry)
                    return render(request, "encyclopedia/search.html", {
                        "results": entries_found,
                        "query": query,
                        "form": SearchForm()
                    })

                    return render(request, "encyclopedia/search.html", {
                        "results": "",
                        "query": "",
                        "form": SearchForm()
                    })

# Edit entry
def editEntry(request, title):
    if request.method == "POST":
        entry = util.get_entry(title) # Get data for the entry to be edited
        edit_form = EditPageForm(initial={'title': title, 'data': entry}) # Display content in textarea

        # Return the page with forms filled with entry information
        return render(request, "encyclopedia/edit.html", {
            "form": SearchForm(),
            "editPageForm": edit_form,
            "entry": entry,
            "title": title
        })


# Submit edit entry
def submitEditEntry(request, title):
    if request.method == "POST":
        edit_entry = EditPageForm(request.POST) # take in data from form
        if edit_entry.is_valid(): # Check if form data is valid (server-side)
            content = edit_entry.cleaned_data["data"] # retrieve 'data' from form
            title_edit = edit_entry.cleaned_data["title"] # get the 'title' from form
            if title_edit != title:  # If the title is edited, delete old file
                filename = f"entries/{title}.md"
                if default_storage.exists(filename):
                    default_storage.delete(filename)

            util.save_entry(title_edit, content) # Saves new entry and redirects to the edited page
            entry = util.get_entry(title_edit) # receive the new entry 
            msg_success = "Updated Successfully!"
    
        # Return the edited entry
        return render(request, "encyclopedia/entry.html", {
            "title": title_edit,
            "entry": markdown2.markdown(entry),
            "form": SearchForm(),
            "msg_success": msg_success
        })

# Randomentry
def randomEntry(request):
    entries = util.list_entries() # retrieve list of all entries
    title = random.choice(entries) # select a title of random selected entry
    entry = util.get_entry(title) # retrieve the content of the selected entry

    # Return the redirect page for the entry
    return HttpResponseRedirect(reverse("entry", args=[title]))
   