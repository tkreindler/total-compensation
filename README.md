# Microsoft Total Compensation

This repo contains a website to easily plot out Total Compensation (TC) at Microsoft over time. It handles contingincies and amorticizes out stock awards and bonusses in a palatable format.

You can generate graphs that look something like this:

<picture>
  <img alt="logo" width="100%" src="https://github.com/tkreindler/total-compensation/blob/master/example.png">
</picture>

This can be very useful for people like Software Engineers with very complex and varying pay over time

# Hosted

A sample instance is hosted at [https://total-compensation.onrender.com/](https://total-compensation.onrender.com/), thank you to the good folks at Render for providing a free tier for projects like this.

There is a backend component to this that sends the data you enter from the frontend to the backend so be aware if you choose to use the sample instance that your provided data is going across the network.
The backend is required for consuming the 'yfinance' python package, it's not possbile to do this in the frontend because yahoo finance doesn't support CORS requests.
It's over a TLS connection and doesn't leave the backend (whose source is in this repo) so it isn't a real issue but I just want to make that clear.
If you don't want your data trusted to the sample instance simply build and run your own server from source.

# Building

For simple changes I recommend just relying on the docker build process. You can use the using the provided [docker-compose.yml](https://github.com/tkreindler/total-compensation/blob/master/docker-compose.yml) file to easily build and run the service.
For more complex changes you'll want to be able to use the provided vscode launch.json configurations. They're extremely elementary and not well set up so I won't get into details but here is some general advide:

- Building with 'npm run build' is extremely slow and makes for painful iterating
    - Run the flask application as usual on port 8000
    - Run 'npm start' to start a second server on port 3000 that supports hot-reloading for frontend changes
    - Temporarily change the api url in [Plot.tsx](https://github.com/tkreindler/total-compensation/blob/master/frontend/src/Plot.tsx) to hit against localhost:8000 where the flask application is hosted
- Change the static root in the flask server's [.env](https://github.com/tkreindler/total-compensation/blob/master/backend/.env) file if you would like

Following these steps you can attach either the frontend or backend debugger using vscode and get a quick reloading experience.

This process could probably be automated way better but I'm no expert with Node or Flask, I'm extremely open to pull requests.

# Potential Improvements

This is just a hobby project so I'm probably gonna leave it as is but there are a lot of potential avenues for improvement:

- Make the form UI not horrible looking
- Add a cpi based inflation line to the chart
    - I initially intended to do this but the 'cpi' python package I usually use for this sort of thing has some issues right now so I didn't do it (yet)
- Support multiple employers in sequence (possibly overlapping)
- Handle more edge cases and strange payment arrangements as people report them

If anyone wants to take a crack at any of these I'm happy to take pull requests.
