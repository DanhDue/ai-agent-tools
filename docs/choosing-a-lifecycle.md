# Choosing a lifecycle

You have a piece of work and three lifecycles to choose from. This page gets you to the right one.

## Start here

Answer one question: **what will exist when you are finished?**

| What you will have produced | Go to |
|---|---|
| Changed code that ships in the build | [If you are writing code](#if-you-are-writing-code) |
| A document someone will read | [If you are writing a document](#if-you-are-writing-a-document) |
| A decision about what to build at all | [If you do not know what to build yet](#if-you-do-not-know-what-to-build-yet) |

If two of those look true at once, pick by the **build**: if any file that ships is changing, it is
code work, however much prose you also write. `doc_quality_check` enforces this and will refuse the
document path outright.

If the whole job is smaller than a review, skip to
[If the work is too small](#if-the-work-is-too-small).
