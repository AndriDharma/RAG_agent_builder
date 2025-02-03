REPOSITORY="demo-2-repo"
IMAGE_NAME="demo-2-image"
PROJECT_ID="dla-gen-ai-specialization"
PROJECT_ID_ENV="844021890758"
INSTANCE_CONNECTION_NAME="dla-gen-ai-specialization:asia-southeast2:db-genai"

REGION="asia-southeast2"
VERSION_ID="latest"
COLLECTION_NAME="default_collection"
ENGINE_NAME="demo2-test_1736323106527"
SERVICE_ACCOUNT="dla-gen-ai@dla-gen-ai-specialization.iam.gserviceaccount.com"

SECRET_ID_DB="db-secret"
SECRET_ID_URL="base_url"
SERVICE_NAME="demo-2-cloud-run"

MIN_INSTANCES=0
MAX_INSTANCES=10

IMAGE="asia-southeast2-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/$IMAGE_NAME"
# Combine environment variables into a single string
ENV_VARS="PROJECT_ID=$PROJECT_ID_ENV,VERSION_ID=$VERSION_ID,SECRET_ID_DB=$SECRET_ID_DB,COLLECTION_NAME=$COLLECTION_NAME,ENGINE_NAME=$ENGINE_NAME"

# # Authenticate with Google Cloud
# echo "Authenticating with Google Cloud..."
# gcloud auth login
# gcloud auth application-default set-quota-project $PROJECT_ID
gcloud config set project $PROJECT_ID

# Build the container image and submit it to Google Container Registry
echo "Building the container image..."
gcloud builds submit --region $REGION --tag $IMAGE

# Deploy the container to Cloud Run
echo "Deploying the container to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --set-env-vars $ENV_VARS \
  --port 8080 \
  --allow-unauthenticated \
  --service-account $SERVICE_ACCOUNT \
  --min-instances $MIN_INSTANCES \
  --max-instances $MAX_INSTANCES \
  --add-cloudsql-instances=$INSTANCE_CONNECTION_NAME

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo "Service deployed to: $SERVICE_URL"