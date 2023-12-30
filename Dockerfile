FROM python:3.12-alpine as backend

RUN pip install --upgrade pip

# copy over backend files
COPY backend/requirements.txt /backend/requirements.txt

# install dependencies
RUN pip install -r /backend/requirements.txt

# install WSGI server
RUN pip install waitress

# copy remaining files
COPY backend/ /backend/

# write static root path
RUN echo "STATIC_ROOT=/frontend/" > /backend/.env


FROM node:20-alpine AS frontend

WORKDIR /build

# copy package files and install dependencies
COPY frontend/package.json /build/package.json
COPY frontend/package-lock.json /build/package-lock.json
RUN npm install

# Copy remaining files and build
COPY frontend/ /build/
RUN npm run build


FROM backend

# copy over frontend from build container
COPY --from=frontend /build/build/* /frontend/

WORKDIR /backend

# run the server
CMD waitress-serve --host 0.0.0.0 --port 8000 app:app
