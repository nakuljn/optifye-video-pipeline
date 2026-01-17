data "aws_vpc" "default" {
  id = "vpc-01c44d43ccc0f5f88"
}

data "aws_subnet" "az1" {
  id = "subnet-0f7013eebcf99d4a4"
}

data "aws_subnet" "az2" {
  id = "subnet-05fc0d85a5994d617"
}

data "aws_subnet" "az3" {
  id = "subnet-06cc4adc8b6bfe2ee"
}

