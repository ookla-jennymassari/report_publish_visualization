# report_publish_visualization
Description:

As a customer I would like an email notification with the rootscore results when they are available so that we can trigger internal groups to review the data.

Need this for the first 2H 2024 market ~ July 20, 2025,

Acceptance Criteria:

Email should be sent at Report Publish

Email should be sent to all the same recipients that get the current consumer report preview - @Gale Kicha can you provide the list.

The required report should be in the body of the email (this can be based on the Rootscore Summary Report) - @Ed Luschei can help flush out the details on this.

We can stop pushing consumer report previews to rootmetrics.com


Workflow:

Wave 1:
- Write the automated email logic 

Wave 2:
- Find the table responsible to update the market status
- Fetch markets for Report Publish 
- Check if email was already sent to the market, if not send email.

Wave 3:

- Create the visualization of email body

Wave 4:
- Determine the recipients and their respective views

Wave 5:
- Automate the email to be sent for each new market in report publish

Wave 6: 

- Create a set up description in README

Information needed on the table:
- csid
- market status
- period
- collection set
