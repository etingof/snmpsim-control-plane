# Utility functions

# Create a REST API resource, return its ID
function create_resource() {
  req=$1
  endpoint=$2

  id=$(curl -d "$req" \
          -H "Content-Type: application/json" \
          -X POST \
          $endpoint | \
       python -c "import sys, json; print(json.load(sys.stdin)['id'])")

  echo $id
}


# Update REST API resource
function update_resource() {
  endpoint=$1

  curl -d "{}" \
      -H "Content-Type: application/json" \
      -X PUT \
      $endpoint
}
