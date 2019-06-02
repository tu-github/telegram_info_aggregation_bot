# Use an official Python runtime as a parent image
FROM python:3-onbuild

# Set the working directory to /app
# WORKDIR /app
#
# Copy the current directory contents into the container at /app
# COPY . /app
#
# Install any needed packages specified in requirements.txt
# RUN pip install --trusted-host pypi.python.org -r requirements.txt
#
# Make port 80 available to the world outside this container
# EXPOSE 80 - WE DO NOT NEED PORTS FOR THE BOT
EXPOSE 5000
# DO NOT USE ALL THAT TO INSTALL DEPENDENCIES AS PYTHON:3-ONBUILD TAKES CARE OF THAT
#
# Define environment variable
# ENV NAME university_events - DO WE NEED THAT?
#
# Run app.py when the container launches

CMD ["python", "./app.py"]
