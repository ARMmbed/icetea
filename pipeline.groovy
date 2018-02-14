def setBuildStatus(String state, String context, String message) {
    step([
        $class: "GitHubCommitStatusSetter",
        reposSource: [
            $class: "ManuallyEnteredRepositorySource",
            url: "https://github.com/ARMmbed/icetea.git"
        ],
        contextSource: [
            $class: "ManuallyEnteredCommitContextSource",
            context: context
        ],
        errorHandlers: [[
            $class: "ChangingBuildStatusErrorHandler",
            result: "UNSTABLE"
        ]],
        commitShaSource: [
            $class: "ManuallyEnteredShaSource",
            sha: env.GIT_COMMIT_HASH
        ],
        statusResultSource: [
            $class: 'ConditionalStatusResultSource',
            results: [
                [
                    $class: 'AnyBuildResult',
                    message: message,
                    state: state
                ]
            ]
        ]
     ])
}


def getGitCommit() {
    if (env.GIT_COMMIT_HASH == null) {
        if (isUnix()) {
            env.GIT_COMMIT_HASH = sh(script: 'git rev-parse HEAD', returnStdout: true).trim()
        }
        else {
            env.GIT_COMMIT_HASH = bat(script: 'git rev-parse HEAD', returnStdout: true).trim()
        }
    }
}


def baseBuild(String platform) {
    execute 'make'

    // get git commit hash
    getGitCommit()

    // run unittest
    String buildName = "unittest in ${platform}"

    setBuildStatus('PENDING', "${buildName}", 'unittest start')
    try {
        stage("${buildName}") {
            execute 'coverage run --parallel-mode -m unittest discover -s test'
        }
        setBuildStatus('SUCCESS', "${buildName}", 'unittest success')
    } catch (Exception e) {
        // set build fail
        setBuildStatus('FAILURE', "${buildName}", "unittests didn't pass")
        currentBuild.result = 'FAILURE'
    }


    // run plugin tests
    String pluginBuildName = "plugin tests in ${platform}"

    setBuildStatus('PENDING', "${pluginBuildName}", 'plugin tests start')
    try {
        stage("${pluginBuildName}") {
            execute 'coverage run --parallel-mode -m unittest discover -s
            icetea_lib/Plugin/plugins/plugin_tests -v'
        }
        setBuildStatus('SUCCESS', "${pluginBuildName}", 'plugin tests success')
    } catch (Exception e) {
        // set build fail
        setBuildStatus('FAILURE', "${pluginBuildName}", "plugin tests didn't pass")
        currentBuild.result = 'FAILURE'
    }


    // Generate Coverage report
    execute 'coverage combine --append'
    execute "coverage html --include='*icetea_lib*' --directory=log_${platform}"
    execute "coverage xml --include='*icetea_lib*' -o log_${platform}/coverage.xml"


    // Archive artifacts
    catchError {
        archiveArtifacts artifacts: "log_${platform}/*.*"
    }


    if (platform == 'linux') {
        catchError {
            // pylint check
            pylint_linux_check()

            // publish warnings checked for console log and pylint log
            warningPublisher('PyLint', '**/pylint.log')
        }

        catchError {
            // Publish cobertura
            step([
                $class: 'CoberturaPublisher',
                coberturaReportFile: 'log_linux/coverage.xml'
            ])
        }
    }


    // Publish HTML reports
    publishHTML(target: [
        allowMissing: false,
        alwayLinkToLastBuild: false,
        keepAll: true,
        reportDir: "log_${platform}",
        reportFiles: "index.html",
        reportName: "${platform} Build HTML Report"
    ])
}

def buildExampleApp() {
    // get git commit hash
    getGitCommit()

    // build app
    String buildName = "build app"
    setBuildStatus('PENDING', "${buildName}", 'start')
    try{
        dir ("examples/cliapp/mbed-os5") {
            sh "mkdir example-app"
            sh "mbed deploy -v"
            sh "mbed compile -t GCC_ARM -m K64F --build BUILD/output | tee example-app/build.log"
            sh "cp BUILD/output/mbed-os5.elf example-app/"
            sh "cp BUILD/output/mbed-os5.bin example-app/"
            archiveArtifacts artifacts: "example-app/**/*"
        }
        setBuildStatus('SUCCESS', "${buildName}", 'success')
    } catch (err) {
        // set build fail
        setBuildStatus('FAILURE', "${buildName}", "fail")
        currentBuild.result = 'FAILURE'
    }
}

def pylint_linux_check() {
    // run pylint check
    String pylintBuildName = "pylint check"

    setBuildStatus('PENDING', "${pylintBuildName}", 'start')
    try {
        echo "REST OF THESE ARE FOR PYLINT"
        sh 'pip install astroid pylint'
        sh 'pylint ./setup.py ./icetea.py ./icetea_lib ./test ./examples > pylint.log ||  exit 0'
        setBuildStatus('SUCCESS', "${pylintBuildName}", 'done')
    } catch (Exception e) {
        // set build fail
        setBuildStatus('FAILURE', "${pylintBuildName}", '')
        currentBuild.result = 'FAILURE'
    }
}


def warningPublisher(String parser, String pattern) {
    step([
        $class: 'WarningsPublisher',
        consoleParsers: [
            [
                parserName: 'GNU Make + GNU C Compiler (gcc)'
            ]
        ],
        parserConfigurations: [
            [
                parserName: parser,
                pattern: pattern
            ]
        ]
    ])

}


return this;
