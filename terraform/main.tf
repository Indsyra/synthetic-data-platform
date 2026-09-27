provider "aws" {
  region = "eu-west-3"
}
resource "aws_s3_bucket" "synthetic_data_bucket" {
  bucket = "indira-synthetic-social-data-2026"
}