import groovy.transform.Field

@Field def projectName = "drools-workbench"           // name of the current application we're running CI/CD for
@Field def branchName = "unknown"                    // name of the current branch to checkout for the application
@Field def buildNumber = "unknown"                   // current Jenkins build number
@Field def devopsBranch = "master"                   // branch for winnow-devops; should always be master, unless for devops testing
@Field def slackChannel = "platform_ci"              // slack channel where the notifications will be pushed
@Field def jobBaseName = "unknown"                   // name of the Jenkins job
@Field def jenkinsSrvName = "unknown"                // name of the Jenkins server
@Field def VERSION = "unknown"                       // application version
@Field def IMAGE = "drools-workbench"        // Docker image name,
@Field def codePath = ""                             // path of application code
@Field def environment = ""                          // environment specifier -- i.e: prod, uat, dynX
@Field def deployable = true                         // variable to check if we should deploy -- currently checks for version diffs between pom.xml and git tag
@Field def service_type = "platform"
@Field def jenkins_node = "jenkins-slave-hub"

try {
    node("$jenkins_node") {
        slackNotifyBuild('PIPELINE STARTED')

        stage('Project setup') {
            dir("app/${projectName}") {
                //checking out the app code
                echo 'Checkout the code..'
                checkout scm
                branchName = env.BRANCH_NAME
                buildNumber = env.BUILD_NUMBER
                jobBaseName = "${env.JOB_NAME}".split('/').last() // We want to get the name of the branch/tag
                jenkinsSrvName = env.BUILD_URL.split('/')[2].split(':')[0]
                echo "Jenkins checkout from branch: $branchName && $buildNumber"
                echo "Running job ${jobBaseName} on jenkins server ${jenkinsSrvName}"
                codePath = pwd()
          }
        }
    }
}
catch (e) {
    // If there was an exception thrown, the build failed
    currentBuild.result = "FAILED"
    slackNotifyBuild("PIPELINE FAILED")
    throw e
}
// figure out next steps depending on the name of the job (which is a git tag)
// x.x.x         -- prod CD
// rc-x.x.x      -- UAT CI/CD
// anything else -- CI
switch (jobBaseName) {
    // PROD tag job
    case ~/^\d+\.\d+\.\d+$/:
        // trigger Jenkinsfile-prod-deploy
        environment = "prod"
        VERSION = "$jobBaseName"
        pipelineCD()
        break
    // UAT tag job
    case ~/^rc-\d+\.\d+\.\d+$/:
        //trigger Jenkinfile-uat-deploy
        VERSION = "$jobBaseName".replaceAll("rc-","")
        echo "Deploy to UAT version: $VERSION"
        environment = "uat"
        pipelineCD()
        break

    default:
        echo "Unfortunatly the deployment of opa is not available for dyn"
        break
}

// This method will help us notify in the slack channel
def slackNotifyBuild(String buildStatus = 'BUILD STARTED') {
    // build status of null means successful
    buildStatus =  buildStatus ?: 'SUCCESSFUL'

    // Default values
    def jobBaseName = "${env.JOB_NAME}".split('/').first()
    def colorName = 'RED'
    def colorCode = '#FF0000'
    def subject = "${buildStatus}: Pipeline `${jobBaseName}` on branch `${env.BRANCH_NAME}` and build `#${env.BUILD_NUMBER}`"
    def summary = "${subject} (${env.BUILD_URL})"

    // Override default values based on build status
    switch (buildStatus) {
        case "BUILD STARTED":
            color = 'YELLOW'
            colorCode = '#FFFF00'
            break
        case "PIPELINE STARTED":
            color = 'YELLOW'
            colorCode = '#FFFF00'
            break
        case "BUILD SUCCESSFUL":
            color = 'BLUE'
            colorCode = '#4186f4'
            break
        case "BUILD UNSTABLE":
            color = 'ORANGE'
            colorCode = '#FF8C00'
            break
        case "DELIVERY STARTED":
            color = 'YELLOW'
            colorCode = '#FFFF00'
            break
        case "DELIVERY SUCCESSFUL":
            color = 'GREEN'
            colorCode = '#30873a'
            break
        case "DEPLOY STARTED":
            color = 'YELLOW'
            colorCode = '#FFFF00'
            break
        case "DEPLOY SUCCESSFUL":
            color = 'BLUE'
            colorCode = '#42f4f4'
            break
        default:
            color = 'RED'
            colorCode = '#FF0000'
            break
    }

    // Send notifications
    if( env.BRANCH_NAME == "dev" || env.BRANCH_NAME == "master" ) {
        slackSend (color: colorCode, message: summary, channel: "${slackChannel}")
    }
}

def pipelineCD(Map args = [:]) {
    node("$jenkins_node") {
        stage('Prepare CD') {
            try {
                dir('app/winnow-devops') {
                    git(
                        poll: true,
                        url: 'git@bitbucket.org:teamwinnow/winnow-devops.git',
                        credentialsId: 'd6e1be13-06a3-4823-8872-2fd509fca9b9',
                        branch: "$devopsBranch"
                    )
                    withEnv(["projectName=$projectName", "jenkins_node=$jenkins_node" ,"service_type=$service_type", "jobBaseName=$jobBaseName", "slackChannel=$slackChannel", "IMAGE=$IMAGE", "environment=$environment", "VERSION=$VERSION", "codePath=$codePath"]) {
                        load "jenkins/files/$service_type/Jenkinsfile-$environment-deploy"
                    }
                }
            } catch (e) {
                throw e
            }
        }
    }
}